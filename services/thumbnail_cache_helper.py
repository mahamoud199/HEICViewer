import os
import sys
import time
import uuid
import ctypes
from ctypes import wintypes
from concurrent.futures import ThreadPoolExecutor

class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8)
    ]

def make_guid(s):
    u = uuid.UUID(s)
    node_bytes = u.node.to_bytes(6, "big")
    d4 = (wintypes.BYTE * 8)(u.clock_seq_hi_variant, u.clock_seq_low, *node_bytes)
    return GUID(u.time_low, u.time_mid, u.time_hi_version, d4)

CLSID_LocalThumbnailCache = make_guid("50EF4544-AC9F-4A8E-B21B-8A26180DB13F")
IID_IThumbnailCache = make_guid("F676C15D-596A-4CE2-8234-33996F445DB1")
IID_IShellItem = make_guid("43826d1e-e718-42ee-bc55-a1e261c37bfe")

def cache_chunk(files_chunk):
    ole32 = ctypes.windll.ole32
    shell32 = ctypes.windll.shell32
    ole32.CoInitialize(None)
    
    p_cache = ctypes.c_void_p()
    hr = ole32.CoCreateInstance(ctypes.byref(CLSID_LocalThumbnailCache), None, 1, ctypes.byref(IID_IThumbnailCache), ctypes.byref(p_cache))
    if hr != 0:
        ole32.CoUninitialize()
        return 0
        
    vtable = ctypes.cast(p_cache, ctypes.POINTER(ctypes.c_void_p))[0]
    get_thumb_ptr = ctypes.cast(vtable, ctypes.POINTER(ctypes.c_void_p))[3]
    get_thumb = ctypes.WINFUNCTYPE(
        ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT, wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p
    )(get_thumb_ptr)
    
    cached = 0
    for fpath in files_chunk:
        p_item = ctypes.c_void_p()
        hr_item = shell32.SHCreateItemFromParsingName(fpath, None, ctypes.byref(IID_IShellItem), ctypes.byref(p_item))
        if hr_item == 0 and p_item.value:
            p_shared_bmp = ctypes.c_void_p()
            out_flags = wintypes.DWORD()
            # WTS_EXTRACT = 0x0 (generates thumbnail & inserts into Windows thumbcache db)
            hr_get = get_thumb(p_cache.value, p_item.value, 256, 0x0, ctypes.byref(p_shared_bmp), ctypes.byref(out_flags), None)
            if hr_get == 0:
                cached += 1
            # Release IShellItem
            vtable_item = ctypes.cast(p_item, ctypes.POINTER(ctypes.c_void_p))[0]
            rel_ptr = ctypes.cast(vtable_item, ctypes.POINTER(ctypes.c_void_p))[2]
            ctypes.WINFUNCTYPE(wintypes.ULONG, ctypes.c_void_p)(rel_ptr)(p_item.value)
            
    # Release IThumbnailCache
    vtable_c = ctypes.cast(p_cache, ctypes.POINTER(ctypes.c_void_p))[0]
    rel_c = ctypes.cast(vtable_c, ctypes.POINTER(ctypes.c_void_p))[2]
    ctypes.WINFUNCTYPE(wintypes.ULONG, ctypes.c_void_p)(rel_c)(p_cache.value)
    
    ole32.CoUninitialize()
    return cached

def main():
    target_folder = r"D:\S\e" if len(sys.argv) < 2 else sys.argv[1]
    if not os.path.exists(target_folder):
        print(f"Folder not found: {target_folder}")
        return

    all_files = [os.path.join(target_folder, f) for f in os.listdir(target_folder) if f.lower().endswith((".heic", ".heif"))]
    total = len(all_files)
    print(f"Found {total} HEIC/HEIF files in {target_folder}. Pre-caching all thumbnails...")
    t0 = time.time()
    
    chunk_size = 20
    chunks = [all_files[i:i+chunk_size] for i in range(0, total, chunk_size)]
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(cache_chunk, chunks))
        
    cached_count = sum(results)
    elapsed = time.time() - t0
    print(f"Cached {cached_count}/{total} thumbnails in {elapsed:.1f}s ({elapsed/total*1000:.1f}ms/img).")
    
    # Notify Windows Explorer
    print("Notifying Windows Explorer...")
    shell32 = ctypes.windll.shell32
    # SHCNE_UPDATEDIR = 0x00001000, SHCNF_PATHW = 0x0005
    shell32.SHChangeNotify(0x00001000, 0x0005, target_folder, None)
    # SHCNE_ASSOCCHANGED = 0x08000000, SHCNF_IDLIST = 0x0000
    shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
    print("Done!")

if __name__ == "__main__":
    main()
