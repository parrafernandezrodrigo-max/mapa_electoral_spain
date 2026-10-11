import sys, re
sys.path.insert(0, '.')
from parser import parse_conv

# Ver qué fichero usa el parser para 202307
import inspect
src = inspect.getsource(parse_conv)
print(src[:800])
