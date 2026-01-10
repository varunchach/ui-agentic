# Conversation Memory Architecture

## Current Implementation

### 1. **Storage Location: Streamlit Session State**

Memory is stored in Streamlit's `session_state` as a list of message dictionaries:

```python
st.session_state.chat_history = [
    {"role": "user", "content": "What is the revenue?"},
    {"role": "assistant", "content": "The revenue is $1.2M..."},
    # ... more messages
]
```

**Location:** `app/ui/main.py` - `initialize_session_state()`

### 2. **Memory Flow Through System**

```
User Query
    ↓
UI (main.py) → Gets chat_history from session_state
    ↓
Orchestrator → Passes chat_history to ChatGraph
    ↓
ChatGraph → Stores in ChatState
    ↓
Q&A Agent → Formats history and includes in LLM prompt
    ↓
ChatGraph → Updates history with new exchange
    ↓
Orchestrator → Returns updated_history
    ↓
UI (main.py) → Updates session_state.chat_history
```

### 3. **History Formatting in Q&A Agent**

**Location:** `app/agents/chat/qa_agent.py` - `_format_history()`

- Takes last **5 exchanges** (10 messages: 5 user + 5 assistant)
- Formats as: `"User: ...\nAssistant: ..."`
- Includes in system prompt under "Previous Conversation:"

```python
def _format_history(self, history: List[Dict[str, str]]) -> str:
    if not history:
        return "No previous conversation."
    
    history_parts = []
    for msg in history[-5:]:  # Last 5 exchanges
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        history_parts.append(f"{role.capitalize()}: {content}")
    
    return "\n".join(history_parts)
```

### 4. **Memory Update Process**

**Location:** `app/agents/graphs/chat_graph.py` - `_combine_results_node()`

After generating answer, history is updated:

```python
chat_history = state.get("chat_history", [])
updated_history = chat_history + [
    {"role": "user", "content": state["query"]},
    {"role": "assistant", "content": answer}
]
state["chat_history"] = updated_history
```

## Current Limitations

### 1. **Session-Only Persistence**
- Memory is **lost** when:
  - User refreshes the page
  - Streamlit session expires
  - Server restarts
- No disk persistence

### 2. **Fixed Window Size**
- Only last **5 exchanges** (10 messages) are sent to LLM
- Older context is ignored
- Can cause loss of important earlier context

### 3. **No Memory Management**
- No token counting
- No intelligent summarization of old messages
- No compression of long conversations

### 4. **Unused ConversationMemory Class**
- `app/utils/memory.py` has a `ConversationMemory` class
- Currently **not integrated** into the system
- Could provide better abstraction

## Memory Structure

### Message Format
```python
{
    "role": "user" | "assistant",
    "content": "Message text"
}
```

### Full History Example
```python
[
    {"role": "user", "content": "What is the revenue?"},
    {"role": "assistant", "content": "The revenue is $1.2M..."},
    {"role": "user", "content": "What about profit?"},
    {"role": "assistant", "content": "The profit is $500K..."},
    # ... continues
]
```

## Integration Points

### 1. **UI Layer** (`app/ui/main.py`)
- **Line 86-87**: Initialize `chat_history` in session_state
- **Line 271**: Get history before query
- **Line 284**: Get updated history from result
- **Line 287**: Update session_state with new history

### 2. **Orchestrator** (`app/agents/orchestrator.py`)
- **Line 105**: Accepts `chat_history` parameter
- **Line 120**: Passes to `chat_graph.run()`

### 3. **Chat Graph** (`app/agents/graphs/chat_graph.py`)
- **Line 300**: Initializes `chat_history` in state
- **Line 179**: Passes to Q&A agent
- **Line 243-248**: Updates history after answer

### 4. **Q&A Agent** (`app/agents/chat/qa_agent.py`)
- **Line 71**: Accepts `chat_history` parameter
- **Line 92**: Formats history for prompt
- **Line 113-115**: Includes in system prompt

## Potential Improvements

### 1. **Persistent Memory**
- Save to disk (JSON/DB) with document_id
- Load on document re-upload
- Session-based or user-based persistence

### 2. **Intelligent Window Management**
- Token-based truncation
- Summarize old messages instead of dropping
- Keep important context (e.g., document summary)

### 3. **Memory Compression**
- Summarize old exchanges
- Keep key facts/decisions
- Reduce token usage while maintaining context

### 4. **Use ConversationMemory Class**
- Integrate `app/utils/memory.py` class
- Better abstraction and methods
- Easier to add features (summarization, etc.)

### 5. **Context-Aware Memory**
- Separate document context from conversation
- Maintain document summary separately
- Better context management

## Current Status

✅ **Working:**
- Memory persists during Streamlit session
- Last 5 exchanges included in prompts
- History properly updated after each query

⚠️ **Limitations:**
- Lost on page refresh
- Fixed 5-exchange window
- No token management
- No summarization

## Code References

- **Storage:** `app/ui/main.py:86-87, 271, 284, 287`
- **Formatting:** `app/agents/chat/qa_agent.py:161-172`
- **Update:** `app/agents/graphs/chat_graph.py:243-248`
- **State:** `app/agents/graphs/state.py:30`
- **Unused Class:** `app/utils/memory.py:9-61`

