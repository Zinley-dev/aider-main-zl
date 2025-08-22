# Fix: Model Parameter Update in Chat API

## Problem
The `/chat` API endpoint was receiving a `model` parameter but wasn't updating it properly, continuing to use the model from the existing session instead.

## Root Cause
In `api_util.py`, the `get_or_create_session` function had a bug in the streaming case where it would create a new coder instance but always use the model from the existing coder (`current_coder.main_model`) instead of checking if a new model was provided.

## Solution
Modified the streaming case in `get_or_create_session` to:
1. Check if the model parameter differs from the current model
2. If different, create a Model instance with the new model
3. Use this new model when creating the new coder instance

## Changes Made
File: `api_util.py`, lines 34-42

```python
# Check if model has changed for streaming requests
current_model_name = current_coder.main_model.name if current_coder.main_model else None
if current_model_name and model and current_model_name != model:
    # Use the new model for streaming requests
    print(f"Model changed from {current_model_name} to {model} for streaming request")
    main_model = Model(model)
else:
    # Use existing model
    main_model = current_coder.main_model
```

## Testing
Run the test script to verify the fix:
```bash
python test_model_update.py
```

This script tests:
1. Creating a session with one model
2. Sending a chat with the same model
3. Sending a chat with a different model (should use the new model)
4. Testing streaming with model change

## Notes
- The non-streaming case was already handling model updates correctly
- The fix ensures that each chat request can specify its own model, even within the same session
- The original session's model is not permanently changed for streaming requests to avoid affecting other concurrent requests