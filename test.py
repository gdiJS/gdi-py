from gdi import V8Engine

engine = V8Engine()
engine.enter()
result = engine.eval("2 + 2")
engine.leave()
print(f"Result: {result}")