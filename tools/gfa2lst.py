#!/usr/bin/env python3
"""gfa2lst.py - turns a tokenized GFA-BASIC (Amiga) .GFA file back into a readable listing.

Usage:  python3 gfa2lst.py PROGRAM.GFA > PROGRAM.LST

The token tables were worked out by comparing GFA files with their ASCII exports.
Tokens that are still unknown are printed as <xx>, <fn2 xx> or <CMD 0xNNNN>.
"""
import struct,sys,math
VT={0xe0:('',0),0xe1:('$',1),0xe2:('%',2),0xe3:('!',3),0xe8:('&',8),0xe9:('|',9),
    0xe4:('(',4),0xe5:('$(',5),0xe6:('%(',6),0xe7:('!(',7),0xec:('&(',12),0xed:('|(',13)}
OPS={0x00:' AND ',0x01:' OR ',0x05:'-',0x06:'+',0x07:'*',0x08:'/',0x09:'^',0x11:'<',0x12:'>',0x13:'=',
     0x14:'<>',0x15:'<=',0x16:'>=',0x1e:'-',0x20:')',0x21:',',0x22:';',0x23:'(',0x5b:'\\',0x0c:'<>',0x0f:'>=',0x0a:' MOD ',0x1f:'NOT ',0x49:' DOWNTO ',0x45:'=',0x4d:'#',0x9d:'(',0x37:'',0x0d:'<=',0x0e:'>=',0x19:'<',0x1a:'>',0x1b:'=',0x1c:'+',0x6d:' OFFSET ',0x39:')=',0x47:' TO ',0x48:' STEP ',0x9c:','}
FN1={0x80:'SPACE$(',0xbe:'STR$(',0x87:'TRIM$(',0x53:'INKEY$',0x6f:'TRACE$',0x59:'AT(',0x42:'CHR$(',0xbc:'TRUE',0xbd:'FALSE',0xb8:'0',0x3f:'MID$(',0x7f:'UPPER$(',0x82:'STRING$(',0x55:'RND',0x2a:'SIN(',0x8a:'L:',0x8b:'W:'}
FN2={0x00:'MUL(',0x42:'LEN(',0x48:'POINT(',0x61:'PRED(',0x43:'ASC(',0x52:'RAND(',0x02:'ADD(',0x60:'SUCC(',0x12:'WINDOW(',0x41:'LPEEK(',0x54:'EXIST(',0xcb:'V:',0x3f:'PEEK(',0x34:'SHL(',0x35:'SHR(',0xce:'STICK(',0xcf:'STRIG(',0x75:'C:'}
JUMP=(0x20,0x04,0xdc,0x10,0xd0,0x40,0x14,0x38,0x30,0xe0)
CMD={0x0:'DO',0x4:'LOOP',0x10:'WHILE',0x14:'WEND',0x1c:'RETURN',0x20:'IF',0x24:'ENDIF',0x28:'FUNCTION',0x2c:'ENDFUNC',
 0x30:'SELECT',0x34:'ENDSELECT',0x38:'ELSE',0x40:'ELSE IF',0x44:'RETURN',0xd0:'LOOP UNTIL',0xd4:'LOCAL',0xd8:'PROCEDURE',
 0xdc:'EXIT IF',0xe0:'CASE',0xe8:'GOTO',0xec:'RESTORE',0xf4:'GOSUB',0xf8:'@',0x11c:'LET',0x160:'PLOT',0x180:'COLOR',
 0x1f0:'END',0x1f4:'LOCATE',0x24c:'PRINT',0x254:'TEXT',0x264:'FORM INPUT',0x26c:'LINE',0x348:'DIM',0x350:'SETCOLOR',
 0x404:'GET',0x410:'PUT',0x434:'CLOSEW',0x44c:'TITLEW',0x458:'GRAPHMODE',0x47c:'BOX',0x480:'PBOX',0x494:'PCIRCLE',
 0x4b0:'FILL',0x4e8:'CLR',0x4ec:'CLS',0x530:'MOUSE',0x570:'POLYFILL',0x5c8:'DRAW',0x5d0:'READ',0x634:'ARRAYFILL',
 0x688:'OPENW',0x6b4:'OPENS',0x6cc:'CLOSES',0x780:'PRBOX',0x668:'OPTION',0x5f4:'DEFINT',0x440:'CLEARW #',0x674:'INLINE',0x508:'ERASE',0x424:'OPEN',0x250:'PRINT',0x430:'CLOSE',0x5c4:'INPUT',0x5c0:'INPUT',0x3c0:'~',0x474:'DEFFILL',0x770:'SCROLL',0x578:'INSERT',0x1b8:'DELAY',0x4c4:'MID$('}
TYPES=['','?','%','!','&','|']  # family order guess: float,?,int,?,word,byte
def gfloat(b):
    m=int.from_bytes(b[:6],'big'); ex=int.from_bytes(b[6:8],'big')
    if m==0: return 0.0
    neg = ex & 0x8000; ex&=0x7ff
    v=m/2**48*2**(ex-0x3fe)
    return -v if neg else v
def fmtnum(v):
    if abs(v-round(v))<1e-9: return str(int(round(v)))
    s=('%.11g'%v); return s
class Dec:
    def __init__(s,fn):
        s.d=d=open(fn,'rb').read()
        e=[struct.unpack('>I',d[i:i+4])[0] for i in range(0x10,0xa4,4)]
        s.e=e; s.T={}; prev=0
        for k in range(18):
            names=[];p=0xa4+prev
            while p<0xa4+e[k]:
                n=d[p];p+=1;names.append(d[p:p+n].decode('latin-1'));p+=n
            s.T[k]=names; prev=e[k]
    def name(s,tab,i):
        t=s.T.get(tab,[])
        return t[i].lower() if i<len(t) else f'?{tab}.{i}'
    def expr(s,b,p,end,base):
        out=[]
        while p<end:
            t=b[p]
            if t==0x46: return ''.join(out),p
            if t in (0xc8,0xc9):
                if t==0xc9: p+=1
                out.append(str(struct.unpack('>i',b[p+1:p+5])[0])); p+=5; continue
            if t in (0xdf,0xdd):
                if t==0xdd: p+=1
                out.append(fmtnum(gfloat(b[p+1:p+9]))); p+=9; continue
            if t==0xde:
                n=b[p+1]; out.append('"'+b[p+2:p+2+n].decode('latin-1')+'"'); p+=2+n; continue
            if t in VT:
                suf,tab=VT[t]; out.append(s.name(tab,b[p+1])+suf); p+=2; continue
            if t==0xea: out.append(s.name(10,b[p+1])); p+=2; continue
            if t==0xee: out.append('@'+s.name(14,b[p+1])); p+=2; continue
            if t==0xd0:
                f=b[p+1]; x=FN2.get(f,f'<fn2 {f:02x}>(')
                if f in (0xcb,0x75): x=x
                out.append(x); p+=2
                if f==0xcb and p<end and b[p] in VT: pass
                continue
            if t in FN1: out.append(FN1[t]); p+=1; continue
            if t in OPS: out.append(OPS[t]); p+=1; continue
            if t==0x9f: p+=1; continue
            if t in (0xca,0xcb,0xcc,0xcd,0xce,0xcf):
                pad=t&1; v=struct.unpack('>I',b[p+1+pad:p+5+pad])[0]
                out.append({0xca:'&H%X',0xcc:'&O%o',0xce:'&X%s'}[t&0xfe].replace('%s','{:b}').format(v) if t&0xfe==0xce else {0xca:'&H%X',0xcc:'&O%o'}[t&0xfe]%v); p+=5+pad; continue
            if t==0xb6: out.append('BASE '); p+=1; continue
            out.append(f'<{t:02x}>'); p+=1
        return ''.join(out),p
    def line(s,b,base):
        c=struct.unpack('>H',b[:2])[0]; p=2; head=None
        if c==0x1cc:
            t=b[2:].split(b'\r')[0].decode('latin-1'); return "'"+(' '+t if t else '')
        if c==0x674:
            ex,q=s.expr(b,2,len(b),base); return 'INLINE '+ex
        if c==0x1d4: return 'DATA '+b[2:].split(b'\r')[0].decode('latin-1')
        if 0x130<=c<=0x15c:
            k=(c-0x130)//4; tabs=[0,1,2,3,8,9,4,5,6,7,12,13]; suf=['','$','%','!','&','|','(','$(','%(','!(','&(','|(']
            i=struct.unpack('>H',b[2:4])[0]; head=s.name(tabs[k],i)+suf[k]; p=4
            if k<6: head+='='
        elif 0x4c<=c<=0x78:
            k=(c-0x4c)//12; i=struct.unpack('>H',b[2:4])[0]; tab=[0,2,8,9][k]; suf=['','%','&','|'][k]
            head='FOR '+s.name(tab,i)+suf+'='; p=4
            if b[p]==0xc9 or b[p]==0x13: pass
        elif 0x7c<=c<=0xa8:
            k=(c-0x7c)//12; i=struct.unpack('>H',b[6:8])[0]; tab=[0,2,8,9][k]; suf=['','%','&','|'][k]
            return 'NEXT '+s.name(tab,i)+suf
        elif 0x280<=c<=0x33c:
            ops=['INC','DEC','ADD','SUB','MUL','DIV']; k=(c-0x280)//0x20; r=((c-0x280)%0x20)//4
            tabs=[0,2,8,9,4,6,12,13]; suf=['','%','&','|','(','%(','&(','|(']
            i=struct.unpack('>H',b[2:4])[0]; head=(ops[k] if k<6 else f'<op{k}>')+' '+s.name(tabs[r],i)+suf[r]; p=4
            if k>=2 or r>=4: head+=('' if r>=4 else ',')
        elif c in (0xf4,0xf0,0xd8):
            i=struct.unpack('>H',b[2:4])[0]; nm=s.name(11,i)
            head={0xf4:'GOSUB ',0xf0:'',0xfc:'@',0xd8:'> PROCEDURE '}[c]+nm; p=4
            if c==0xd8 and b[4]!=0x46: head+='('
        elif c in JUMP:
            head=CMD[c]; p=6
            if c in (0x04,0x14,0x38): return head
        elif c==0xf8:
            i=struct.unpack('>H',b[2:4])[0]; head='@'+s.name(11,i); p=4
        elif c==0xfc and b[2]==0xea:
            return s.name(10,b[3])+':'
        elif c==0xe8:
            return 'GOTO '+s.name(10,b[3])
        elif 0x100<=c<=0x12c:
            k=(c-0x100)//4; tabs=[0,1,2,3,8,9,4,5,6,7,12,13]; suf=['','$','%','!','&','|','(','$(','%(','!(','&(','|(']
            i=struct.unpack('>H',b[2:4])[0]; head='LET '+s.name(tabs[k],i)+suf[k]; p=4
            if k<6: head+='='
        elif c==0x28 and b[2]==0xee:
            head='FUNCTION '+s.name(14,b[3]); p=4
        elif c==0xec:
            return 'RESTORE '+s.name(10,b[3])
        else:
            head=CMD.get(c,f'<CMD {c:#06x}>'); p=2
            if c in (0x688,0x44c,0x434,0x250,0xb4,0x24c) and b[2] in (0xc8,0xc9) and c!=0x24c: head+=' #'
        ex,q=s.expr(b,p,len(b),base)
        txt=head+(('' if head.endswith(('=',',','(','#','~')) or not ex or ex.startswith('(') or ex.startswith(')') else ' ')+ex)
        q+=1
        if (base+q)%2: q+=1
        if q<len(b):
            sp=b[q]; cm=b[q+1:].split(b'\r')[0].decode('latin-1')
            txt+=' '*max(1,sp)+'!'+cm
        return txt
    def indent(s,lines):
        out=[];lvl=0
        opn=('DO','WHILE','IF ','FOR ','SELECT','> PROCEDURE','FUNCTION')
        cls=('LOOP','WEND','ENDIF','NEXT','ENDSELECT','RETURN','ENDFUNC')
        mid=('ELSE','CASE','DEFAULT')
        for l in lines:
            w=l.split(' ')[0]
            if l.startswith(('> PROCEDURE','FUNCTION')): lvl=0
            if l.startswith(cls) and not (l.startswith('RETURN ') and lvl>1): lvl=max(0,lvl-1)
            if l.startswith('RETURN ') : pass
            ind=lvl-1 if l.startswith(mid) else lvl
            out.append('  '*max(0,ind)+l if not l.startswith(('> PROCEDURE','FUNCTION')) else l)
            if l.startswith(opn) or l=='DO': lvl+=1
            if l.startswith('RETURN') and l.strip()=='RETURN': lvl=0
            if l=='ENDFUNC': lvl=0
        return out
    def run(s,start_tab=17,out=sys.stdout):
        d=s.d; p=0xa4+s.e[start_tab]; end=0xa4+s.e[18]; res=[]
        while p<end:
            n=struct.unpack('>H',d[p:p+2])[0]
            if n==0: break
            try: res.append(s.line(d[p+2:p+n],p+2))
            except Exception as ex: res.append(f'<ERR {ex}> '+d[p+2:p+n].hex())
            p+=n
        return res
if __name__=='__main__':
    D=Dec(sys.argv[1]); 
    st=17
    while st>0 and D.e[st-1]==D.e[17]: st-=1
    L=[l for l in D.run(int(sys.argv[2]) if len(sys.argv)>2 else 15) if not l.startswith('<ERR')]
    for l in D.indent(L): print(l)
