"""Servidor FALSO do SAP 3.0 com o repasse do versionamento, para as provas do plugin.

Responde, só em memória e só no endereço de loopback que o sistema escolher,
às rotas que o SAP Operador usa numa atividade versionada (tipo 4) e no
pacote de um servidor antigo, do tipo 2 (modo `recusa`), que o plugin recusa: login, `distribuicao/verifica`, `distribuicao/finaliza` (409 com
`sessao_id` enquanto houver conflito), microcontrole, e o repasse
`/api/versionamento/servico/*` com as rotas do serviço (info, datasets, model,
extent, features em JSON e na página binária DSGP/1, salvamento com recusa por
campo, status, undo, history, lineage, split e fuse com a recusa do motivo
ausente ou em branco, sessões, resolve com a recusa da justificativa em
branco, 409 como o serviço).

A página DSGP/1 é montada por `encode_page`, conferida pelo decodificador do
próprio plugin (`modules/versionamento/feature_page.py`) em `checar_codificador`.

Suposições do contrato que este servidor encena (contrato-sap.md):
- o 409 do `finaliza` vem no envelope do SAP: `{message, dados: {sessao_id, repo_id, conflitos}}`,
  com `repo_id` onde a sessão mora: o PAI no merge, o próprio clone no pull
  (`server/src/versionamento/ciclo_atividade.js`); o servidor só responde a
  sessão nesse repositório, e o repasse deixa o operador ler e resolver nela;
- o SAP põe `X-Dsg-Actor`; o plugin não manda `actor` no corpo.
"""
import copy
import hashlib
import json
import struct
import threading
import uuid
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import parse_qs,urlsplit

MEDIA_TYPE='application/vnd.dsg.features.v1'
TYPES={'Point':1,'LineString':2,'Polygon':3,'MultiPoint':4,'MultiLineString':5,'MultiPolygon':6}
REQUIRED=['batch_write','children','discard','extent','features_bbox','features_ids','merge_closes_clone',
          'save_request_id','shallow_clone','undo_last_save','uuid_identity','error_codes']
SERVICE='/api/versionamento/servico'
USER='operador.teste'


# DSGP/1 ---------------------------------------------------------------------------

def _rings(geometry):
    """[[ring de pontos] por parte] e o código do tipo."""
    kind=geometry['type']; c=geometry['coordinates']
    if kind=='Point': return [[[c]]]
    if kind=='LineString': return [[c]]
    if kind=='Polygon': return [c]
    if kind=='MultiPoint': return [[[p]] for p in c]
    if kind=='MultiLineString': return [[line] for line in c]
    if kind=='MultiPolygon': return c
    raise ValueError(kind)


def encode_page(spec,features,generation,next_cursor):
    """Página DSGP/1 (codificação f64, sem geometria de mapa) de `features`."""
    names=[f['name'] for f in spec['fields']]
    attributes={'ids':[f['id'] for f in features],'columns':{n:[f['properties'].get(n) for f in features] for n in names}}
    coordinates=[];rings=[0];parts=[0];offsets=[0];dims=3 if spec.get('z') else 2
    for feature in features:
        geometry=feature.get('geometry')
        if geometry:
            for part in _rings(geometry):
                for ring in part:
                    for point in ring: coordinates.extend(float(v) for v in point[:dims])
                    rings.append(len(coordinates)//dims)
                parts.append(len(rings)-1)
        offsets.append(len(parts)-1)
    sections=[json.dumps(attributes,ensure_ascii=False).encode('utf-8'),
              struct.pack('<'+str(len(coordinates))+'d',*coordinates),
              struct.pack('<'+str(len(rings))+'I',*rings),struct.pack('<'+str(len(parts))+'I',*parts),
              struct.pack('<'+str(len(offsets))+'I',*offsets)]
    body=b'';places=[]
    for index,data in enumerate(sections):
        body+=b'\0'*(-len(body)%8)
        places.append([len(body),len(data)]); body+=data
    head={'version':1,'count':len(features),'generation':generation,'dataset':spec['name'],'next':next_cursor,
          'schema':hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest(),'attributes':places[0],
          'source':{'type':TYPES.get(spec.get('geometry_type'),0),'dimensions':dims,'srid':int(spec.get('srid') or 4326),
                    'encoding':'f64','coordinates':places[1],'rings':places[2],'parts':places[3],'features':places[4]},'map':None}
    text=json.dumps(head,separators=(',',':')).encode('utf-8'); text+=b' '*(-len(text)%8)
    return b'DSGP'+struct.pack('<I',len(text))+text+body


def _bounds(geometry):
    points=[p for part in _rings(geometry) for ring in part for p in ring]
    return min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)


# Dados de teste -------------------------------------------------------------------

def square(x,y,size=0.01):
    return {'type':'Polygon','coordinates':[[[x,y],[x+size,y],[x+size,y+size],[x,y+size],[x,y]]]}


def _id():
    return str(uuid.uuid4())


class Estado:
    """Repositórios, feições, sessões e o registro de tudo que chegou."""

    def __init__(self,modo='versionado'):
        self.modo=modo
        self.token='tok-'+uuid.uuid4().hex
        self.lock=threading.RLock()
        self.pedidos=[]
        self.bloco=_id(); self.atividade=_id(); self.sessao='sessao-'+uuid.uuid4().hex[:8]
        # Onde a sessão do conflito mora, como o SAP diz no `repo_id` do 409
        # (ciclo_atividade.js): o pai no merge, o próprio clone no pull.
        self.sessao_repo=self.bloco
        self.generation=10
        self.specs={
            'cobter_massa_dagua_a':{'name':'cobter_massa_dagua_a','geometry_type':'Polygon','srid':4674,'z':False,'fields':[
                {'name':'nome','kind':'text','nullable':True},{'name':'tipo_massa_dagua','kind':'integer','nullable':True},
                {'name':'subfase_id','kind':'integer','nullable':True}]},
            'aux_revisao_p':{'name':'aux_revisao_p','geometry_type':'Point','srid':4674,'z':False,'fields':[
                {'name':'descricao','kind':'text','nullable':True},{'name':'subfase_id','kind':'integer','nullable':True},
                {'name':'situacao_correcao','kind':'integer','nullable':True},{'name':'justificativa','kind':'text','nullable':True}]},
            # A grade de revisão do versionado mora no clone da atividade (a
            # camada está na subfase): a ferramenta de revisão a abre pelo
            # provedor e grava nela a grade nova.
            'aux_grid_revisao_a':{'name':'aux_grid_revisao_a','geometry_type':'Polygon','srid':4674,'z':False,'fields':[
                {'name':'rank','kind':'integer','nullable':True},{'name':'visited','kind':'boolean','nullable':True},
                {'name':'atividade_id','kind':'integer','nullable':True},{'name':'unidade_trabalho_id','kind':'integer','nullable':True},
                {'name':'etapa_id','kind':'integer','nullable':True}]},
        }
        # Recusa a gravação na grade de revisão (permissão da etapa), para a
        # prova da recusa mostrada ao operador.
        self.recusar_grade=False
        self.f1=_id(); self.f2=_id(); self.f3=_id(); self.p1=_id(); self.p2=_id()
        self.features={
            'cobter_massa_dagua_a':{
                self.f1:{'id':self.f1,'properties':{'nome':'Lago A','tipo_massa_dagua':1,'subfase_id':7},'geometry':square(-51.0,-30.0)},
                self.f2:{'id':self.f2,'properties':{'nome':'Lago B','tipo_massa_dagua':None,'subfase_id':7},'geometry':square(-50.98,-30.0)},
                self.f3:{'id':self.f3,'properties':{'nome':'Lago C','tipo_massa_dagua':2,'subfase_id':7},'geometry':square(-50.96,-30.0)}},
            'aux_revisao_p':{
                self.p1:{'id':self.p1,'properties':{'descricao':'da subfase','subfase_id':7,'situacao_correcao':None,'justificativa':None},
                         'geometry':{'type':'Point','coordinates':[-50.99,-29.995]}},
                self.p2:{'id':self.p2,'properties':{'descricao':'de outra subfase','subfase_id':8,'situacao_correcao':None,'justificativa':None},
                         'geometry':{'type':'Point','coordinates':[-50.97,-29.995]}}},
            'aux_grid_revisao_a':{},
        }
        self.saves=[]; self.history=[]; self.lineage={}
        base={'id':self.f1,'properties':{'nome':'Lago A','tipo_massa_dagua':1,'subfase_id':7},'geometry':square(-51.0,-30.0)}
        self.items=[{'dataset':'cobter_massa_dagua_a','feature_id':self.f1,'status':'conflict',
                     'conflicts':[{'field':'nome','reason':'both_changed'}],'base':base,
                     'ours':dict(copy.deepcopy(base),properties=dict(base['properties'],nome='Lago A do bloco')),
                     'theirs':dict(copy.deepcopy(base),properties=dict(base['properties'],nome='Lago A da atividade')),'result':None}]
        self.decisoes=[]; self.resolucoes_recusadas=[]; self.linhagens_recusadas=[]; self.finalizacoes=[]; self.microcontrole=[]
        # Ajuste do pacote antes de responder (variantes de tipo e de campos).
        self.ajuste=None

    # pacote ---------------------------------------------------------------------
    def pacote(self):
        regras={'grupo_estilo':[{'tipo_estilo':'Preencher atributo','cor_rgb':'255,170,0'}],
                'regras':[{'tipo_estilo':'Preencher atributo','descricao':'Tipo de massa d água vazio','regra':'"tipo_massa_dagua" is null',
                           'atributo':'tipo_massa_dagua','camadas':['edgv.cobter_*']}]}
        qml=('<!DOCTYPE qgis PUBLIC "http://mrcc.com/qgis.dtd" "SYSTEM"><qgis version="4.0.0" styleCategories="Symbology">'
             '<renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0"><symbols>'
             '<symbol type="fill" name="0" alpha="1" clip_to_extent="1" force_rhr="0"><layer class="SimpleFill" enabled="1" locked="0" pass="0">'
             '<Option type="Map"><Option type="QString" name="color" value="0,90,200,255"/></Option></layer></symbol></symbols></renderer-v2></qgis>')
        atividade={
            'id':101,'unidade_trabalho_id':55,'etapa_id':9,'tipo_etapa_id':1,'subfase_id':7,'tipo_fase_id':1,
            'nome':'Aquisição de hidrografia','unidade_trabalho':'UT-TESTE-1','projeto':'Projeto teste','lote':'Lote teste',
            'bloco':'Bloco teste','subtipo_produto':'Carta topográfica','denominador_escala':25000,
            'geom':'SRID=4674;POLYGON((-51.02 -30.02,-50.9 -30.02,-50.9 -29.95,-51.02 -29.95,-51.02 -30.02))',
            'dado_producao':{'tipo_dado_producao_id':4 if self.modo=='versionado' else 2},
            'camadas':[{'schema':'edgv','nome':'cobter_massa_dagua_a','documentacao':'https://exemplo.invalid/doc/cobter'},
                       {'schema':'edgv','nome':'aux_revisao_p','camada_apontamento':True,'atributo_filtro_subfase':'subfase_id',
                        'atributo_situacao_correcao':'situacao_correcao','atributo_justificativa_apontamento':'justificativa'}],
            'estilos':[{'f_table_schema':'edgv','f_table_name':'cobter_massa_dagua_a','stylename':'padrao','styleqml':qml}],
            'alias':[{'definicao_alias':json.dumps([{'camadaNome':'cobter_massa_dagua_a','camadaApelido':'',
                                                      'atributosApelido':[{'nome':'nome','alias':'Nome da massa d água'}]}])}],
            'regras':[{'regra':json.dumps(regras,ensure_ascii=False)}],
            'temas':[{'nome':'Hidrografia','definicao_tema':json.dumps([{'nome':'Hidrografia','camadas':[{'schema':'edgv','camada':'cobter_massa_dagua_a'}]}])}],
            'menus':[],'workflow_dsgtools':[],'models_qgis':[],
            # Insumo de banco PostGIS (tipo de insumo 3), fictício: o plugin não o abre mais.
            'insumos':[{'id':1,'nome':'insumo_banco','caminho':'banco.invalid:5432/insumos/edgv/cobter_massa_dagua_a','epsg':'4674',
                        'tipo_insumo_id':3,'caminho_padrao':None}],'fme':[],'monitoramento':[1],'linhagem':[],
            'atalhos':[],'colunas_ocultas':[],'requisitos':[],'observacao_atividade':None,
        }
        dados={'login':USER,'usuario_uuid':str(uuid.UUID(int=1)),'atividade':atividade}
        if self.modo=='versionado':
            dados['versionamento']={'repo_id':self.atividade,'servico':SERVICE,'papel':'atividade',
                                    'datasets':[{'schema':'edgv','nome':n,'dataset':n} for n in self.specs]}
        else:
            # Tipo 2 de um servidor antigo: banco de produção fictício (domínio
            # reservado .invalid) e a credencial efêmera.
            atividade['dado_producao']['configuracao_producao']='banco.invalid:5432/producao_teste'
            dados['login_info']={'login':'usuario_banco','senha':'senha_ficticia'}
        if self.ajuste:
            dados=self.ajuste(dados) or dados
        return dados

    # serviço --------------------------------------------------------------------
    def model(self):
        return {'digest':'d'*64,'domains':{'tipo_massa_dagua':[{'code':1,'label':'Lago (1)'},{'code':2,'label':'Represa (2)'}]},
                'classes':{'cobter_massa_dagua_a':{'identity':{'kind':'uuid','field':'id'},
                                                   'fields':{'tipo_massa_dagua':{'domain':'tipo_massa_dagua'},'nome':{'max_length':80}}}}}

    def page(self,dataset,q):
        rows=sorted(self.features[dataset].values(),key=lambda f:f['id'])
        if q.get('ids'):
            wanted=set(json.loads(q['ids'])); rows=[f for f in rows if f['id'] in wanted]
        if q.get('bbox'):
            x0,y0,x1,y1=[float(v) for v in q['bbox'].split(',')]
            rows=[f for f in rows if f.get('geometry') and not (lambda b:b[2]<x0 or b[0]>x1 or b[3]<y0 or b[1]>y1)(_bounds(f['geometry']))]
        after=q.get('after') or ''
        rows=[f for f in rows if f['id']>after]
        limit=int(q.get('limit') or 500)
        nxt=rows[limit-1]['id'] if len(rows)>limit else None
        return rows[:limit],nxt

    def save(self,repo,body):
        dataset=body['dataset']
        if body.get('expected_generation')!=self.generation:
            return 409,{'error':'Geração vencida.','code':'stale_generation'}
        violations=[]
        for feature in (body.get('inserts') or [])+(body.get('updates') or []):
            if (feature.get('properties') or {}).get('nome')=='PROIBIDO':
                violations.append({'dataset':dataset,'id':feature['id'],'field':'nome','code':'permission',
                                   'detail':'campo nome não é editável na etapa desta atividade'})
        if dataset=='aux_grid_revisao_a' and self.recusar_grade:
            violations+=[{'dataset':dataset,'id':feature['id'],'field':None,'code':'permission',
                          'detail':'a etapa desta atividade não permite inserir feição em aux_grid_revisao_a'}
                         for feature in body.get('inserts') or []]
        if violations:
            return 409,{'error':'Salvamento recusado.','code':'model_violation','violations':violations}
        before={}
        for feature in body.get('inserts') or []: before[feature['id']]=None; self.features[dataset][feature['id']]=feature
        for feature in body.get('updates') or []:
            before[feature['id']]=copy.deepcopy(self.features[dataset].get(feature['id'])); self.features[dataset][feature['id']]=feature
        for identity in body.get('deletes') or []:
            before[identity]=self.features[dataset].pop(identity,None)
        self.generation+=1
        self.saves.append({'dataset':dataset,'before':before})
        for identity,state in before.items():
            self.history.append({'seq':len(self.history)+1,'dataset':dataset,'feature_id':identity,'actor':USER,
                                 'occurred_at':'2026-10-13T12:00:00Z','before':state,'after':self.features[dataset].get(identity),
                                 'operation':'insert' if state is None else 'delete' if identity not in self.features[dataset] else 'update'})
        return 200,{'generation':self.generation,'revision':uuid.uuid4().hex}

    def undo(self,body):
        if body.get('expected_generation')!=self.generation:
            return 409,{'error':'Geração vencida.','code':'stale_generation'}
        if not self.saves: return 409,{'error':'Nada a desfazer.','code':'nothing_to_undo'}
        last=self.saves.pop()
        for identity,state in last['before'].items():
            current=self.features[last['dataset']].get(identity)
            if state is None: self.features[last['dataset']].pop(identity,None)
            else: self.features[last['dataset']][identity]=state
            # O desfazer é um salvamento novo: entra no histórico.
            self.history.append({'seq':len(self.history)+1,'dataset':last['dataset'],'feature_id':identity,'actor':USER,
                                 'occurred_at':'2026-10-13T12:05:00Z','before':current,'after':state,
                                 'operation':'delete' if state is None else 'insert' if current is None else 'update'})
        self.generation+=1
        return 200,{'generation':self.generation,'features':len(last['before'])}

    def lineage_op(self,operation,body):
        # Como o serviço real (service/src/lineage_ops.rs, `reason`): o motivo
        # ausente, não texto ou em branco é 409, antes da geração e da classe.
        if not isinstance(body.get('reason'),str) or not body['reason'].strip():
            self.linhagens_recusadas.append(dict(body,operation=operation))
            return 409,{'error':'Motivo obrigatório: a operação de linhagem registra por que a feição original deixou de existir.'}
        dataset=body['dataset']
        if body.get('expected_generation')!=self.generation:
            return 409,{'error':'Geração vencida.','code':'stale_generation'}
        before={}
        if operation=='split':
            original=self.features[dataset].pop(body['id']); before[body['id']]=original; created=[]
            for part in body['parts']:
                identity=_id(); created.append(identity); before[identity]=None
                self.features[dataset][identity]={'id':identity,'properties':part['properties'],'geometry':part['geometry']}
            self.lineage[body['id']]={'operation':'split','successors':created,'reason':body.get('reason','')}
            answer={'parts':created}
        else:
            identity=_id(); before[identity]=None
            for old in body['ids']: before[old]=self.features[dataset].pop(old)
            self.features[dataset][identity]={'id':identity,'properties':body['result']['properties'],'geometry':body['result']['geometry']}
            for old in body['ids']: self.lineage[old]={'operation':'fuse','successors':[identity],'reason':body.get('reason','')}
            answer={'result':identity}
        self.generation+=1
        self.saves.append({'dataset':dataset,'before':before})
        return 200,dict(answer,generation=self.generation)


class Handler(BaseHTTPRequestHandler):
    estado=None

    def log_message(self,*args): pass

    def _send(self,status,payload,content_type='application/json'):
        data=payload if isinstance(payload,bytes) else json.dumps(payload,ensure_ascii=False).encode('utf-8')
        self.send_response(status); self.send_header('Content-Type',content_type); self.send_header('Content-Length',str(len(data)))
        self.end_headers(); self.wfile.write(data)

    def _body(self):
        size=int(self.headers.get('Content-Length') or 0)
        raw=self.rfile.read(size) if size else b''
        return json.loads(raw.decode('utf-8')) if raw else None

    def do_GET(self): self._route('GET')
    def do_POST(self): self._route('POST')
    def do_PUT(self): self._route('PUT')

    def _route(self,method):
        estado=self.estado; url=urlsplit(self.path)
        q={k:v[-1] for k,v in parse_qs(url.query,keep_blank_values=True).items()}
        body=self._body() if method!='GET' else None
        with estado.lock:
            estado.pedidos.append({'method':method,'path':url.path,'query':q,'body':body,
                                   'authorization':self.headers.get('Authorization'),'actor_header':self.headers.get('X-Dsg-Actor')})
            path=url.path
            if path=='/api/login' and method=='POST':
                return self._send(200,{'version':'3.32.0','success':True,'message':'ok','dados':{'token':estado.token}})
            auth=self.headers.get('Authorization') or ''
            if auth.replace('Bearer ','')!=estado.token:
                return self._send(401,{'version':'3.32.0','success':False,'message':'Token inválido'})
            if path=='/api/distribuicao/verifica':
                return self._send(200,{'version':'3.32.0','success':True,'message':'ok','dados':estado.pacote()})
            if path=='/api/distribuicao/finaliza':
                estado.finalizacoes.append(body)
                pending=[i for i in estado.items if i['status']=='conflict']
                if estado.modo=='versionado' and pending:
                    return self._send(409,{'version':'3.32.0','success':False,'message':'A integração da atividade tem conflitos.',
                                           'dados':{'sessao_id':estado.sessao,'repo_id':estado.sessao_repo,
                                                    'conflitos':[{'dataset':i['dataset'],'id':i['feature_id']} for i in pending]}})
                return self._send(200,{'version':'3.32.0','success':True,'message':'Atividade finalizada com sucesso.'})
            if path.startswith('/api/microcontrole/'):
                estado.microcontrole.append(body)
                return self._send(200,{'version':'3.32.0','success':True,'message':'ok'})
            if path.startswith(SERVICE+'/'):
                return self._service(method,path[len(SERVICE):],q,body)
            return self._send(404,{'message':'Rota ausente no servidor falso: '+path})

    def _service(self,method,path,q,body):
        estado=self.estado
        if path=='/info':
            return self._send(200,{'service':{'version':'falso'},'auth':'sap','identity':'sap',
                                   'capabilities':REQUIRED+['features_dsgp1','repository_model','save_violations','lineage','history_operation'],
                                   'limits':{'batch_operations':1000}})
        parts=path.strip('/').split('/')
        if parts[0]!='repos' or len(parts)<3:
            return self._send(404,{'error':'Rota ausente.'})
        repo=parts[1]; rest=parts[2:]
        if repo not in (estado.atividade,estado.bloco):
            return self._send(403,{'error':'Repositório fora do alcance do operador.'})
        if repo==estado.bloco and rest[0]!='sessions':
            return self._send(403,{'error':'O operador só lê sessões no repositório pai.'})
        key=(method,rest[0])
        if key==('GET','datasets'): return self._send(200,{'datasets':list(estado.specs.values())})
        if key==('GET','model'):
            if q.get('known')=='d'*64: return self._send(200,{'model':{'digest':'d'*64,'unchanged':True},'required':{}})
            return self._send(200,{'model':estado.model(),'required':{}})
        if key==('GET','status'):
            return self._send(200,{'repo_id':repo,'generation':estado.generation,'parent_id':estado.bloco,'closed':None})
        if key==('GET','extent'):
            rows=list(estado.features[q['dataset']].values())
            boxes=[_bounds(f['geometry']) for f in rows if f.get('geometry')]
            extent=[min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)] if boxes else None
            return self._send(200,{'generation':estado.generation,'count':len(rows),'extent':extent})
        if key==('GET','features'):
            rows,nxt=estado.page(q['dataset'],q)
            if q.get('format')=='dsgp1':
                return self._send(200,encode_page(estado.specs[q['dataset']],rows,estado.generation,nxt),MEDIA_TYPE)
            return self._send(200,{'generation':estado.generation,'next':nxt,'items':[{'feature':f} for f in rows]})
        if key==('POST','features'): return self._send(*estado.save(repo,body))
        if key==('POST','undo'): return self._send(*estado.undo(body))
        if key==('GET','history'):
            events=[e for e in estado.history if e['dataset']==q.get('dataset') and (not q.get('id') or e['feature_id']==q['id'])]
            return self._send(200,{'events':events,'next':None})
        if key==('GET','lineage'):
            found=estado.lineage.get(q.get('id'))
            successors=[{'operation':found['operation'],'successors':[{'id':s,'alive':True} for s in found['successors']],
                         'actor':USER,'at':'2026-10-13T12:00:00Z','reason':found['reason']}] if found else []
            return self._send(200,{'predecessors':[],'successors':successors})
        if key==('POST','lineage') and len(rest)==2: return self._send(*estado.lineage_op(rest[1],body))
        if rest[0]=='sessions' and len(rest)>=2 and rest[1]==estado.sessao and repo==estado.sessao_repo:
            # A sessão do PULL mora no clone (destino): `ours` é o que a
            # atividade gravou e `theirs` o bloco, como o serviço real responde
            # (medido no roteiro de ponta a ponta do controle_acervo). A do
            # merge mora no bloco, com os lados ao contrário.
            pull=repo==estado.atividade
            if method=='GET' and len(rest)==2:
                return self._send(200,{'id':estado.sessao,'mode':'pull' if pull else 'push','state':'prepared',
                                       'target_id':repo,'source_id':estado.bloco if pull else estado.atividade})
            if method=='GET' and rest[2:]==['items']:
                items=[i for i in estado.items if q.get('conflicts')!='true' or i['status']=='conflict']
                if pull: items=[dict(i,ours=i['theirs'],theirs=i['ours']) for i in items]
                return self._send(200,{'items':items,'next':None,'counts':{'conflict':sum(1 for i in estado.items if i['status']=='conflict')}})
            if method=='POST' and rest[2:]==['resolve']:
                # Como o serviço real: `reason` ausente é 404 (sync_ops.rs `resolve`),
                # e o que não é texto, ou é texto em branco, 409 (exchange.rs `resolve`).
                if 'reason' not in body:
                    return self._send(404,{'error':'Parâmetro ausente: reason.','code':'missing_parameter'})
                if not isinstance(body['reason'],str) or not body['reason'].strip():
                    estado.resolucoes_recusadas.append(body)
                    return self._send(409,{'error':'Justificativa obrigatória para resolução.'})
                item=next(i for i in estado.items if i['feature_id']==body['id'] and i['dataset']==body['dataset'])
                item['status']='resolved'; item['result']=body['result']; estado.decisoes.append(body)
                return self._send(200,{'resolved':True})
        return self._send(404,{'error':'Rota ausente no servidor falso: '+method+' '+path})


def iniciar(modo='versionado'):
    """Sobe o servidor em thread, no loopback e em porta livre. Devolve (servidor, estado, url base)."""
    estado=Estado(modo)
    handler=type('H',(Handler,),{'estado':estado})
    server=ThreadingHTTPServer(('127.0.0.1',0),handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server,estado,'http://127.0.0.1:'+str(server.server_address[1])


def checar_codificador(decode):
    """O codificador deste servidor contra o decodificador do plugin: devolve as feições lidas."""
    estado=Estado()
    spec=estado.specs['cobter_massa_dagua_a']; rows=sorted(estado.features['cobter_massa_dagua_a'].values(),key=lambda f:f['id'])
    page=decode(encode_page(spec,rows,estado.generation,None))
    assert [i['feature']['id'] for i in page['items']]==[f['id'] for f in rows]
    assert page['items'][0]['feature']['geometry']['coordinates']==rows[0]['geometry']['coordinates']
    assert page['items'][0]['feature']['properties']==rows[0]['properties']
    return page
