"""Prints the model names your API key can use. Run: python list_models.py
Add --test to try a tiny chat request on likely models and see which ones really work.
Never prints the key. Copy one name into OPENAI_MODEL in .env."""
import sys
import time

from openai import OpenAI

from druk.config import ENV_FILE, env_help, get_api_key, get_base_url, get_model

key = get_api_key()
if not key or key == "your-api-key-here":
    raise SystemExit("No usable API key. " + env_help())

print(f"Reading settings from: {ENV_FILE}")
print(f"Base URL: {get_base_url() or 'default OpenAI'}")
print(f"Current OPENAI_MODEL: {get_model()}\n")
try:
    names = sorted(m.id.removeprefix("models/") for m in OpenAI(api_key=key, base_url=get_base_url()).models.list())
except Exception as exc:  # show the provider's message, hiding the key if it appears
    raise SystemExit("Could not list models: " + str(exc).replace(key, "[hidden]")[:300])
print("Models available to your key (try one with 'flash' in the name):")
print("\n".join(names))

if "--test" in sys.argv:
    skip = ("embed", "tts", "image", "imagen", "live", "audio", "veo", "robotics", "computer", "aqa", "vision")
    candidates = [n for n in names if ("flash" in n or "gemma" in n) and not any(w in n for w in skip)]
    client = OpenAI(api_key=key, base_url=get_base_url())
    print(f"\nTesting {min(len(candidates), 12)} models with a tiny chat request (uses a little free quota)...")
    for name in candidates[:12]:
        try:
            client.chat.completions.create(model=name, messages=[{"role": "user", "content": "Say OK"}])
            print("  WORKS :", name)
        except Exception as exc:
            detail = " ".join(str(exc).replace(key, "[hidden]").split())[:110]
            print("  fails :", name, "-", detail)
        time.sleep(1)
    print("\nUse a name marked WORKS as OPENAI_MODEL in .env.")
else:
    print("\nTip: run 'python list_models.py --test' to find which of these actually work for chat.")
