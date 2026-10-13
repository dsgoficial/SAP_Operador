"""Compara dois rastros do cenário `tipo2` de prova_qgis.py (HEAD e árvore de trabalho).

Uso: python comparar_rastros.py <rastro_head.json> <rastro_novo.json>
Sai com 1 e diz o primeiro ponto divergente quando o fluxo antigo mudou.
"""
import json
import sys

KEYS=('processing','banco','ferramentas','stubs','acoes_de_camada','mensagens','camadas','checks')


def main(head,new):
    a=json.load(open(head,encoding='utf-8')); b=json.load(open(new,encoding='utf-8'))
    if a.get('erro') or b.get('erro'):
        print('rastro com erro:',(a.get('erro') or b.get('erro')).strip().splitlines()[-1]); return 1
    for key in KEYS:
        if a.get(key)!=b.get(key):
            left=a.get(key) or []; right=b.get(key) or []
            if isinstance(left,list) and isinstance(right,list):
                index=next((i for i,(x,y) in enumerate(zip(left,right)) if x!=y),min(len(left),len(right)))
                print('diverge em',key,'item',index)
                print(' HEAD:',json.dumps(left[index] if index<len(left) else None,ensure_ascii=False)[:800])
                print(' novo:',json.dumps(right[index] if index<len(right) else None,ensure_ascii=False)[:800])
            else:
                print('diverge em',key)
            return 1
    print('rastros iguais:',len(a['processing']),'chamadas de processing,',', '.join(KEYS))
    return 0


if __name__=='__main__':
    sys.exit(main(sys.argv[1],sys.argv[2]))
