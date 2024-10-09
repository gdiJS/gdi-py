import ctypes
import os
import sys
from ctypes import c_bool, c_char_p, c_int, c_uint, c_int64, c_double, c_void_p, CFUNCTYPE

def is_64bit_python():
    return sys.maxsize > 2**32

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Determine the correct DLL name based on Python architecture
dll_name = 'engine64.dll' if is_64bit_python() else 'engine32.dll'
dll_path = os.path.join(script_dir, dll_name)

print(f"Python architecture: {'64-bit' if is_64bit_python() else '32-bit'}")
print(f"Looking for DLL at: {dll_path}")

# Check if the DLL file exists
if not os.path.exists(dll_path):
    raise FileNotFoundError(f"The DLL file '{dll_name}' does not exist in the script directory.")

# Load the DLL
try:
    v8_dll = ctypes.CDLL(dll_path)
    print(f"DLL '{dll_name}' loaded successfully")
except OSError as e:
    raise OSError(f"Failed to load the DLL: {e}")

# Define constants
V8_ERROR = 0
V8_RANGE_ERROR = 1
V8_REFERENCE_ERROR = 2
V8_SYNTAX_ERROR = 3
V8_TYPE_ERROR = 4

# Define types
V8Isolate = c_void_p
V8Context = c_void_p
V8String = c_void_p
V8Object = c_void_p
V8ObjectTemplate = c_void_p
V8FunctionCallbackInfo = c_void_p

# Define function prototype for V8FunctionCallback
V8FunctionCallback = CFUNCTYPE(None, V8FunctionCallbackInfo)

# Function declarations
v8_init = v8_dll.v8_init
v8_init.restype = c_bool

v8_cleanup = v8_dll.v8_cleanup
v8_cleanup.restype = None

v8_new_isolate = v8_dll.v8_new_isolate
v8_new_isolate.restype = V8Isolate

v8_destroy_isolate = v8_dll.v8_destroy_isolate
v8_destroy_isolate.argtypes = [V8Isolate]

v8_enter_isolate = v8_dll.v8_enter_isolate
v8_enter_isolate.argtypes = [V8Isolate]

v8_leave_isolate = v8_dll.v8_leave_isolate
v8_leave_isolate.argtypes = [V8Isolate]

v8_new_context = v8_dll.v8_new_context
v8_new_context.argtypes = [V8Isolate]
v8_new_context.restype = V8Context

v8_enter_context = v8_dll.v8_enter_context
v8_enter_context.argtypes = [V8Context]

v8_leave_context = v8_dll.v8_leave_context
v8_leave_context.argtypes = [V8Context]

v8_destroy_context = v8_dll.v8_destroy_context
v8_destroy_context.argtypes = [V8Context]

v8_eval_asstr = v8_dll.v8_eval_asstr
v8_eval_asstr.argtypes = [V8Isolate, V8Context, ctypes.c_wchar_p]
v8_eval_asstr.restype = V8String

v8_strinfo = v8_dll.v8_strinfo
v8_strinfo.argtypes = [V8String, ctypes.POINTER(c_int)]
v8_strinfo.restype = ctypes.c_wchar_p

v8_destroy_string = v8_dll.v8_destroy_string
v8_destroy_string.argtypes = [V8String]

# Helper function to convert V8String to Python string
def v8_string_to_python(v8_str):
    length = c_int()
    ptr = v8_strinfo(v8_str, ctypes.byref(length))
    result = ptr[:length.value]
    v8_destroy_string(v8_str)
    return result

class V8Engine:
    def __init__(self):
        print("Initializing V8Engine")
        self.isolate = None
        self.context = None
        try:
            self.isolate = v8_new_isolate()
            if not self.isolate:
                raise RuntimeError("Failed to create V8 isolate")
            print("V8 isolate created successfully")
            
            v8_enter_isolate(self.isolate)
            self.context = v8_new_context(self.isolate)
            if not self.context:
                raise RuntimeError("Failed to create V8 context")
            print("V8 context created successfully")
            
            v8_leave_isolate(self.isolate)
        except Exception as e:
            print(f"Error during initialization: {e}")
            self.cleanup()
            raise

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        print("Cleaning up V8Engine")
        if hasattr(self, 'context') and self.context:
            v8_destroy_context(self.context)
            print("V8 context destroyed")
        if hasattr(self, 'isolate') and self.isolate:
            v8_destroy_isolate(self.isolate)
            print("V8 isolate destroyed")

    def enter(self):
        if self.isolate and self.context:
            v8_enter_isolate(self.isolate)
            v8_enter_context(self.context)

    def leave(self):
        if self.isolate and self.context:
            v8_leave_context(self.context)
            v8_leave_isolate(self.isolate)

    def eval(self, code):
        if not (self.isolate and self.context):
            raise RuntimeError("V8Engine not properly initialized")
        v8_result = v8_eval_asstr(self.isolate, self.context, code)
        if v8_result:
            return v8_string_to_python(v8_result)
        return None

print("Initializing V8")
if not v8_init():
    raise RuntimeError("Failed to initialize V8")
print("V8 initialized successfully")

# Example usage
if __name__ == "__main__":
    try:
        engine = V8Engine()
        engine.enter()
        result = engine.eval("2 + 2")
        engine.leave()
        print(f"Result: {result}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Cleaning up V8")
        v8_cleanup()
        print("V8 cleanup completed")