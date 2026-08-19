from tools.groq_utils import create_chat_completion

try:
    stream = create_chat_completion(messages=[{"role": "user", "content": "Stream test: say hello."}], stream=True)
    print('Stream object type:', type(stream))
    count = 0
    for chunk in stream:
        count += 1
        try:
            print('--- CHUNK', count, '---')
            print(repr(chunk))
            # Try to show choices/delta if present
            choices = getattr(chunk, 'choices', None)
            if choices:
                delta = getattr(choices[0], 'delta', None)
                if delta:
                    print('delta.content:', getattr(delta, 'content', None))
        except Exception as e:
            print('Chunk read error:', type(e).__name__, e)
    print('Done, total chunks:', count)
except Exception as e:
    print('Create stream error:', type(e).__name__, e)
