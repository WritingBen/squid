# MANDATORY REQUIREMENTS FOR CLAUDE

## TESTING PROTOCOL - NON-NEGOTIABLE

### For ANY UI/Visual Change:

1. **BEFORE claiming any UI change is complete, you MUST:**
   - Capture a screenshot using `app.export_screenshot()`
   - Save it to a file
   - Read/examine the screenshot content
   - Explicitly describe what you see in the screenshot
   - Confirm EACH specific visual requirement is met

2. **FORBIDDEN phrases until visual proof is captured:**
   - "Fixed"
   - "Working"
   - "Complete"
   - "Verified"
   - "Should work"
   - "Appears to"
   - "Seems to"
   - "Might be"
   - "Probably"

3. **Automated tests are NOT sufficient for UI changes:**
   - pytest passing does NOT prove visual correctness
   - You MUST capture and examine visual output
   - Every visual claim requires visual evidence

### For ANY Functionality Change:

1. **You MUST:**
   - Actually run the code that exercises the functionality
   - Capture output/evidence of it working
   - Describe specifically what happened
   - Confirm the expected behavior occurred

2. **"Cannot verify" is FAILURE:**
   - If you cannot verify something, you have not completed the task
   - Find a way to verify or ask the user for help
   - Never accept unverified changes as complete

### Verification Checklist (MUST complete for each change):

```
[ ] Change made
[ ] Code runs without errors
[ ] Visual screenshot captured (for UI changes)
[ ] Screenshot examined and described
[ ] Each requirement explicitly confirmed with evidence
[ ] No forbidden phrases used without proof
```

## CONSEQUENCES OF VIOLATION

If you skip visual verification for UI changes:
- You are lying to the user
- You are wasting the user's time
- You are betraying the user's trust
- The user will have to repeat themselves AGAIN

## REMEMBER

The user has repeatedly asked you to follow this protocol. You have repeatedly failed. This file exists because your word cannot be trusted. Prove yourself through actions, not promises.
