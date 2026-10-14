"""GeoPackage de campo FALSO: o clone da atividade em arquivo, como o serviço o entrega (9.1).

Reproduz, para as provas do modo local do tipo 4, o que o adaptador GeoPackage
do serviço (controle_acervo, `versionamento/backend/storage-gpkg/src/ddl.rs` e
`class.rs`) grava num clone, no que o QGIS toca ao editar o arquivo:

- a tabela de trabalho de cada classe se chama `f_` + 20 dígitos hexadecimais
  do SHA-256 do nome da classe, com `fid INTEGER PRIMARY KEY AUTOINCREMENT`,
  `dsg_id TEXT NOT NULL UNIQUE` com o CHECK do UUID canônico e os campos; o
  nome da classe vai em `gpkg_contents.identifier` e em `dsg_classes.name`;
- a tabela de versões `v_<h>` e os gatilhos de captura (inserção, atualização,
  exclusão), com as guardas de identidade imutável, de fid e de clone
  encerrado, copiados do `capture_triggers`; os gatilhos da R*Tree do
  GeoPackage 1.4, que chamam as funções `ST_` registradas pelo GDAL;
- `dsg_meta` com `family`, `format_version`, `repo_id`, `parent_id` e
  `permissions` (texto canônico do codec), `dsg_seq` e `dsg_revisions`: as
  versões pendentes são `dsg_seq.last` menos o maior `seq_last` das revisões,
  como `Repository::pending_versions`.

Não é o arquivo que o serviço gera (o serviço não roda nesta máquina): é a
parte do formato que o plugin exercita. A prova de ponta a ponta com o clone
de verdade fica com a frente que sobe o serviço.
"""
import hashlib
import json
import sqlite3
import struct

from osgeo import ogr,osr

UUID_CHECK="(typeof(dsg_id) = 'text' AND length(dsg_id) = 36 AND dsg_id GLOB '{0}-{1}-{2}-{3}-{4}')".format(
    *['[0-9a-f]'*n for n in (8,4,4,4,12)])
UNATTRIBUTED='external:unattributed'
CLOSED_MESSAGE='Clone encerrado (merge ou descarte): ele não aceita mais edição; abra um clone novo a partir do pai (D026).'


def q(name):
    return '"'+name.replace('"','""')+'"'


def lit(text):
    return "'"+text.replace("'","''")+"'"


def sufixo(nome):
    return hashlib.sha256(nome.encode('utf-8')).hexdigest()[:20]


def tabela(nome):
    """Tabela de trabalho da classe no GeoPackage do clone (class.rs, table_suffix)."""
    return 'f_'+sufixo(nome)


def _blob(wkt,srid):
    geometry=ogr.CreateGeometryFromWkt(wkt)
    minx,maxx,miny,maxy=geometry.GetEnvelope()
    header=b'GP'+bytes([0,0x03])+struct.pack('<i',srid)+struct.pack('<4d',minx,maxx,miny,maxy)
    return header+bytes(geometry.ExportToWkb(ogr.wkbNDR)),(minx,maxx,miny,maxy)


def _capture(t,v,cols,rev=1):
    tn=t; vn=v; t=q(t); v=q(v)
    quoted=[q(c) for c in cols]
    actor='coalesce((SELECT actor FROM dsg_context WHERE k = 1), {0})'.format(lit(UNATTRIBUTED))
    attribution='coalesce((SELECT attribution FROM dsg_context WHERE k = 1), 0)'
    capturing='coalesce((SELECT suppress FROM dsg_context WHERE k = 1), 0) = 0'
    at="strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"
    seq='(SELECT last FROM dsg_seq WHERE k = 1)'
    bump='UPDATE dsg_seq SET last = last + 1 WHERE k = 1;'
    head='dsg_seq, dsg_op, dsg_actor, dsg_at, dsg_attribution, dsg_schema_rev, dsg_id'
    full=head+(', '+', '.join(quoted) if quoted else '')
    new='NEW.dsg_id'+(', '+', '.join('NEW.'+c for c in quoted) if quoted else '')
    insert_op='CASE WHEN (SELECT dsg_op FROM {0} WHERE dsg_id = NEW.dsg_id ORDER BY dsg_seq DESC LIMIT 1) IN (1, 2) THEN 2 ELSE 1 END'.format(v)
    changed=' OR '.join('OLD.{0} IS NOT NEW.{0}'.format(c) for c in quoted) or '0'
    closed="EXISTS (SELECT 1 FROM dsg_meta WHERE key = 'closure')"
    refuse=lambda message:'SELECT RAISE(ABORT, {0});'.format(lit(message))
    out=[]
    for event,suffix in (('INSERT','insert'),('UPDATE','update'),('DELETE','delete')):
        out.append('CREATE TRIGGER {0} BEFORE {1} ON {2}\nWHEN {3}\nBEGIN {4} END'.format(
            q(tn+'_dsg_closed_'+suffix),event,t,closed,refuse(CLOSED_MESSAGE)))
    out.append('CREATE TRIGGER {0} BEFORE UPDATE OF dsg_id ON {1}\nWHEN NEW.dsg_id IS NOT OLD.dsg_id\nBEGIN {2} END'.format(
        q(tn+'_dsg_identity'),t,refuse('A identidade persistente dsg_id é imutável.')))
    out.append('CREATE TRIGGER {0} BEFORE INSERT ON {1}\nWHEN EXISTS (SELECT 1 FROM {1} WHERE fid = NEW.fid AND dsg_id IS NOT NEW.dsg_id)\nBEGIN {2} END'.format(
        q(tn+'_dsg_fid_insert'),t,refuse('O fid pertence a outra identidade persistente; exclua-a explicitamente antes.')))
    out.append('CREATE TRIGGER {0} BEFORE UPDATE OF fid ON {1}\nWHEN NEW.fid IS NOT OLD.fid AND EXISTS (SELECT 1 FROM {1} WHERE fid = NEW.fid)\nBEGIN {2} END'.format(
        q(tn+'_dsg_fid_update'),t,refuse('O fid pertence a outra identidade persistente; exclua-a explicitamente antes.')))
    out.append('CREATE TRIGGER {0} AFTER INSERT ON {1}\nWHEN {2}\nBEGIN\n  {3}\n  INSERT INTO {4}({5})\n  VALUES ({6}, {7}, {8}, {9}, {10}, {11}, {12});\nEND'.format(
        q(tn+'_dsg_insert'),t,capturing,bump,v,full,seq,insert_op,actor,at,attribution,rev,new))
    out.append('CREATE TRIGGER {0} AFTER UPDATE ON {1}\nWHEN ({2}) AND {3}\nBEGIN\n  {4}\n  INSERT INTO {5}({6})\n  VALUES ({7}, 2, {8}, {9}, {10}, {11}, {12});\nEND'.format(
        q(tn+'_dsg_update'),t,changed,capturing,bump,v,full,seq,actor,at,attribution,rev,new))
    out.append('CREATE TRIGGER {0} AFTER DELETE ON {1}\nWHEN {2}\nBEGIN\n  {3}\n  INSERT INTO {4}({5})\n  VALUES ({6}, 3, {7}, {8}, {9}, {10}, OLD.dsg_id);\nEND'.format(
        q(tn+'_dsg_delete'),t,capturing,bump,v,head,seq,actor,at,attribution,rev))
    out.append('CREATE TRIGGER {0} BEFORE UPDATE ON {1}\nBEGIN {2} END'.format(q(vn+'_dsg_immutable_update'),v,refuse('Versões são imutáveis.')))
    out.append('CREATE TRIGGER {0} BEFORE DELETE ON {1}\nBEGIN {2} END'.format(q(vn+'_dsg_immutable_delete'),v,refuse('Versões são imutáveis.')))
    out.append('CREATE TRIGGER {0} BEFORE INSERT ON {1}\nWHEN NEW.dsg_seq IS NULL OR NEW.dsg_seq < 1 OR NEW.dsg_seq > {2}\nBEGIN {3} END'.format(
        q(vn+'_dsg_reserved_seq'),v,seq,refuse('Versões só são gravadas pela captura ou pela integração do DSG Versioning.')))
    return out


def _rtree(t,c):
    rn='rtree_{0}_{1}'.format(t,c); r=q(rn); t=q(t); c=q(c)
    values=lambda row:'{0}.fid, ST_MinX({0}.{1}), ST_MaxX({0}.{1}), ST_MinY({0}.{1}), ST_MaxY({0}.{1})'.format(row,c)
    present=lambda row:'({0}.{1} NOTNULL AND NOT ST_IsEmpty({0}.{1}))'.format(row,c)
    absent=lambda row:'({0}.{1} ISNULL OR ST_IsEmpty({0}.{1}))'.format(row,c)
    name=lambda s:q(rn+'_'+s)
    return rn,[
        'CREATE TRIGGER {0} AFTER INSERT ON {1} WHEN (new.{2} NOT NULL AND NOT ST_IsEmpty(NEW.{2})) BEGIN INSERT OR REPLACE INTO {3} VALUES ({4}); END'.format(name('insert'),t,c,r,values('NEW')),
        'CREATE TRIGGER {0} AFTER UPDATE OF {1} ON {2} WHEN OLD.fid = NEW.fid AND {3} AND {4} BEGIN UPDATE {5} SET minx = ST_MinX(NEW.{1}), maxx = ST_MaxX(NEW.{1}), miny = ST_MinY(NEW.{1}), maxy = ST_MaxY(NEW.{1}) WHERE id = NEW.fid; END'.format(name('update6'),c,t,present('NEW'),present('OLD'),r),
        'CREATE TRIGGER {0} AFTER UPDATE OF {1} ON {2} WHEN OLD.fid = NEW.fid AND {3} AND {4} BEGIN INSERT INTO {5} VALUES ({6}); END'.format(name('update7'),c,t,present('NEW'),absent('OLD'),r,values('NEW')),
        'CREATE TRIGGER {0} AFTER UPDATE OF {1} ON {2} WHEN OLD.fid = NEW.fid AND {3} BEGIN DELETE FROM {4} WHERE id = OLD.fid; END'.format(name('update2'),c,t,absent('NEW'),r),
        'CREATE TRIGGER {0} AFTER UPDATE ON {1} WHEN OLD.fid != NEW.fid AND {2} BEGIN DELETE FROM {3} WHERE id = OLD.fid; INSERT OR REPLACE INTO {3} VALUES ({4}); END'.format(name('update5'),t,present('NEW'),r,values('NEW')),
        'CREATE TRIGGER {0} AFTER UPDATE ON {1} WHEN OLD.fid != NEW.fid AND {2} BEGIN DELETE FROM {3} WHERE id IN (OLD.fid, NEW.fid); END'.format(name('update4'),t,absent('NEW'),r),
        'CREATE TRIGGER {0} AFTER DELETE ON {1} WHEN old.{2} NOT NULL BEGIN DELETE FROM {3} WHERE id = OLD.fid; END'.format(name('delete'),t,c,r),
    ]


def permissoes_canonicas(permissions):
    """Texto de `permissions` como o codec grava (chaves ordenadas)."""
    return json.dumps(permissions,sort_keys=True,separators=(',',':'),ensure_ascii=False)


def criar(path,repo_id,parent_id,classes,permissions=None,srid=4674,modelo=None,meta_extra=None):
    """Cria o GeoPackage do clone. `classes`: [{name, geometry: 'POINT'|'POLYGON', fields:
    [(nome, tipo declarado)], rows: [{dsg_id, wkt, <campo>: valor}]}]. `modelo`: o
    documento `dsg-model/1` (dict) gravado em `dsg_model`, como o clone o recebe da raiz."""
    driver=ogr.GetDriverByName('GPKG')
    ds=driver.CreateDataSource(str(path)); ds=None
    db=sqlite3.connect(str(path),isolation_level=None)
    srs=osr.SpatialReference(); srs.ImportFromEPSG(srid)
    if not db.execute('SELECT 1 FROM gpkg_spatial_ref_sys WHERE srs_id=?',(srid,)).fetchone():
        db.execute("INSERT INTO gpkg_spatial_ref_sys(srs_name,srs_id,organization,organization_coordsys_id,definition) VALUES (?,?,'EPSG',?,?)",
                   ('SIRGAS 2000',srid,srid,srs.ExportToWkt()))
    db.executescript('''
    CREATE TABLE IF NOT EXISTS gpkg_extensions (table_name TEXT, column_name TEXT, extension_name TEXT NOT NULL,
      definition TEXT NOT NULL, scope TEXT NOT NULL, CONSTRAINT ge_tce UNIQUE (table_name, column_name, extension_name));
    CREATE TABLE dsg_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE dsg_context (k INTEGER PRIMARY KEY CHECK (k = 1), actor TEXT NOT NULL,
      attribution INTEGER NOT NULL DEFAULT 1 CHECK (attribution IN (1, 2)), suppress INTEGER NOT NULL DEFAULT 0 CHECK (suppress IN (0, 1)));
    CREATE TABLE dsg_seq (k INTEGER PRIMARY KEY CHECK (k = 1), last INTEGER NOT NULL);
    INSERT INTO dsg_seq VALUES (1, 0);
    CREATE TABLE dsg_classes (class_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, table_name TEXT NOT NULL UNIQUE,
      version_table TEXT NOT NULL UNIQUE, spec TEXT NOT NULL, schema_rev INTEGER NOT NULL);
    CREATE TABLE dsg_revisions (rev_seq INTEGER PRIMARY KEY, id TEXT NOT NULL UNIQUE, parents TEXT NOT NULL, actor TEXT NOT NULL,
      at TEXT NOT NULL, message TEXT NOT NULL, kind TEXT NOT NULL, received_from TEXT, seq_first INTEGER, seq_last INTEGER);
    ''')
    meta={'family':'dsg-versioning','format_version':'4','required_features':'[]','repo_id':repo_id,'parent_id':parent_id,
          'schema_generation':'1','created_at':'2026-10-13T12:00:00.000Z'}
    if permissions is not None: meta['permissions']=permissoes_canonicas(permissions)
    meta.update(meta_extra or {})
    if modelo is not None:
        texto=json.dumps(modelo,separators=(',',':'),ensure_ascii=False)
        db.execute('CREATE TABLE dsg_model (k INTEGER PRIMARY KEY CHECK (k = 1), name TEXT NOT NULL, version TEXT NOT NULL, digest TEXT NOT NULL, document TEXT NOT NULL)')
        db.execute('INSERT INTO dsg_model VALUES (1,?,?,?,?)',(modelo['name'],modelo['version'],hashlib.sha256(texto.encode('utf-8')).hexdigest(),texto))
    db.executemany('INSERT INTO dsg_meta VALUES (?,?)',list(meta.items()))
    seq=0; triggers=[]
    for class_id,spec in enumerate(classes,start=1):
        t=tabela(spec['name']); v='v_'+sufixo(spec['name']); geom='geom'
        geometry_type=spec['geometry']
        columns=['fid INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL','dsg_id TEXT NOT NULL UNIQUE CHECK '+UUID_CHECK]
        columns+=[q(name)+' '+kind for name,kind in spec['fields']]+[q(geom)+' '+geometry_type]
        db.execute('CREATE TABLE {0} (\n  {1})'.format(q(t),',\n  '.join(columns)))
        names=[name for name,_ in spec['fields']]+[geom]
        version_columns=['dsg_seq INTEGER PRIMARY KEY NOT NULL','dsg_id TEXT NOT NULL','dsg_op INTEGER NOT NULL','dsg_actor TEXT NOT NULL',
                         'dsg_at TEXT NOT NULL','dsg_attribution INTEGER NOT NULL','dsg_schema_rev INTEGER NOT NULL']
        version_columns+=[q(name)+' '+kind for name,kind in spec['fields']]+[q(geom)+' '+geometry_type]
        version_columns+=['dsg_revision INTEGER','dsg_origin TEXT','dsg_origin_seq INTEGER','dsg_prev_origin TEXT','dsg_prev_seq INTEGER','dsg_received_from TEXT']
        db.execute('CREATE TABLE {0} (\n  {1})'.format(q(v),',\n  '.join(version_columns)))
        kinds={'TEXT':'text','INTEGER':'integer','REAL':'real','BOOLEAN':'boolean'}
        spec_fields=[{'name':name,'kind':kinds.get(kind,'text'),'nullable':True} for name,kind in spec['fields']]
        spec_fields.append({'name':geom,'kind':'geometry','geometry_type':geometry_type.title(),'srid':srid,'z':False,'nullable':True})
        db.execute('INSERT INTO dsg_classes VALUES (?,?,?,?,?,1)',(class_id,spec['name'],t,v,json.dumps({'fields':spec_fields})))
        db.execute("INSERT INTO gpkg_contents(table_name,data_type,identifier,description,srs_id) VALUES (?, 'features', ?, '', ?)",(t,spec['name'],srid))
        db.execute("INSERT INTO gpkg_contents(table_name,data_type,identifier,description,srs_id) VALUES (?, 'features', ?, ?, ?)",
                   (v,spec['name']+' (versões)','Histórico DSG Versioning, somente leitura',srid))
        for table in (t,v):
            db.execute('INSERT INTO gpkg_geometry_columns VALUES (?,?,?,?,0,0)',(table,geom,geometry_type,srid))
        rn,rtree_triggers=_rtree(t,geom)
        db.execute('CREATE VIRTUAL TABLE {0} USING rtree(id, minx, maxx, miny, maxy)'.format(q(rn)))
        db.execute("INSERT INTO gpkg_extensions VALUES (?, ?, 'gpkg_rtree_index', 'http://www.geopackage.org/spec120/#extension_rtree', 'write-only')",(t,geom))
        for row in spec.get('rows') or []:
            blob,box=_blob(row['wkt'],srid)
            values=[row['dsg_id']]+[row.get(name) for name,_ in spec['fields']]+[blob]
            cursor=db.execute('INSERT INTO {0}(dsg_id,{1}) VALUES ({2})'.format(q(t),','.join(q(n) for n in names),','.join('?' for _ in values)),values)
            fid=cursor.lastrowid
            db.execute('INSERT INTO {0} VALUES (?,?,?,?,?)'.format(q(rn)),(fid,)+box)
            seq+=1
            db.execute('INSERT INTO {0}(dsg_seq,dsg_id,dsg_op,dsg_actor,dsg_at,dsg_attribution,dsg_schema_rev,{1}) VALUES (?,?,1,?,?,1,1,{2})'.format(
                q(v),','.join(q(n) for n in names),','.join('?' for _ in names)),
                [seq,row['dsg_id'],'sap:clone','2026-10-13T12:00:00.000Z']+values[1:])
        triggers+=_capture(t,v,names)+rtree_triggers
    db.execute('UPDATE dsg_seq SET last=?',(seq,))
    db.execute("INSERT INTO dsg_revisions VALUES (1,?,'[]','sap','2026-10-13T12:00:00.000Z','clone','clone',?,?,?)",
               ('00000000-0000-4000-8000-000000000001',parent_id,1 if seq else None,seq or None))
    for sql in triggers: db.execute(sql)
    db.execute('PRAGMA journal_mode=WAL')
    db.close()
    return path


def pendentes(path):
    """Versões ainda não cobertas por revisão (Repository::pending_versions)."""
    db=sqlite3.connect(str(path))
    try:
        last=db.execute('SELECT last FROM dsg_seq WHERE k = 1').fetchone()[0]
        done=db.execute('SELECT coalesce(max(seq_last), 0) FROM dsg_revisions WHERE seq_last IS NOT NULL').fetchone()[0]
        return last-done
    finally:
        db.close()


def versoes(path,nome):
    """(dsg_op, dsg_id, dsg_actor) das versões da classe, em ordem."""
    db=sqlite3.connect(str(path))
    try:
        return db.execute('SELECT dsg_op,dsg_id,dsg_actor FROM {0} ORDER BY dsg_seq'.format(q('v_'+sufixo(nome)))).fetchall()
    finally:
        db.close()
