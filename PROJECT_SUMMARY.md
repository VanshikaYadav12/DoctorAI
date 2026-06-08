# DoctorAI Project Summary

## Project Overview

DoctorAI is an AI hospital appointment booking backend built with:

- FastAPI
- PostgreSQL
- SQLModel
- Alembic
- Twilio Voice
- ngrok

The system lets a patient call a Twilio number, speak their health issue, get routed to the correct hospital department, choose a doctor, provide their name, choose a date/time, and book an appointment if the slot is available.

## Current Main Flow

1. Patient calls the Twilio number.
2. Twilio sends the call to:

   ```text
   POST /voice
   ```

3. AI says:

   ```text
   Welcome to Akashwani Hospital. Please tell me your health issue.
   ```

4. Patient says a health problem, for example:

   ```text
   I have skin allergy
   I have heart pain
   I have severe headache
   I have knee pain
   My child has fever
   ```

5. Backend detects the department.

6. Backend fetches doctors from PostgreSQL for that department.

7. AI reads available doctors and asks:

   ```text
   Which doctor would you prefer?
   ```

8. Patient says the doctor name.

9. AI asks for the patient full name.

10. Patient says their name.

11. AI spells the name and asks for confirmation.

12. If patient says yes, AI asks for appointment date/time.

13. If patient says no, AI asks the patient to spell the name.

14. Patient gives appointment date/time.

15. Backend checks:

   - doctor exists
   - slot is available
   - appointment conflict does not exist

16. If available, AI asks for slot confirmation.

17. If patient confirms, appointment is saved.

18. AI says:

   ```text
   Your appointment has been booked successfully.
   ```

## Department Detection

The voice system currently detects these departments:

- Cardiology
- Dermatology
- Neurology
- Pediatrics
- Orthopedics

Examples:

```text
heart pain -> Cardiology
skin allergy -> Dermatology
severe headache -> Neurology
child fever -> Pediatrics
knee pain -> Orthopedics
```

The department detection logic lives in:

```text
app/api/call_routes.py
```

## Appointment Booking

Appointments are stored in:

```text
appointments
```

The appointment table now stores:

- patient_name
- patient_phone
- appointment_time
- status
- notes
- doctor_id
- doctor_name
- created_at

`doctor_name` was added so it is easy to see which doctor the appointment is scheduled with without manually joining the doctors table.

## Call Tracking Added

The following call tracking models were added or fixed:

```text
CallLog
CallConversation
CallTranscript
CallRecording
```

### CallLog

Stores:

- call_sid
- caller_number
- call_status
- started_at
- ended_at
- duration_seconds
- created_at

### CallConversation

Stores every user and AI message:

- call_sid
- speaker
- message
- timestamp

The speaker is:

```text
USER
AI
```

### CallTranscript

Stores complete transcript generated from `CallConversation` rows:

- call_sid
- complete_transcript
- created_at

### CallRecording

Stores Twilio recording URLs:

- call_sid
- recording_url
- created_at

## API Endpoints

### Main App

```text
GET /
```

Returns health/status message.

### Doctors

```text
POST /doctors/
GET /doctors/
GET /doctors/{doctor_id}
PATCH /doctors/{doctor_id}
DELETE /doctors/{doctor_id}
```

### Appointments

```text
POST /appointments/
GET /appointments/
GET /appointments/{appointment_id}
PATCH /appointments/{appointment_id}
DELETE /appointments/{appointment_id}
```

### Twilio Voice

```text
POST /voice
GET /voice
POST /twilio
GET /twilio
POST /process-speech
POST /call-status
POST /recording-status
```

`/twilio` is kept as an alias for `/voice` in case Twilio is accidentally configured with `/twilio`.

## Important Files Changed

### Voice Flow

```text
app/api/call_routes.py
```

Major changes:

- Rebuilt Twilio state machine.
- Added department detection.
- Added doctor selection flow.
- Added patient name confirmation.
- Added spelling correction flow.
- Added appointment date/time confirmation.
- Added slot availability check.
- Added appointment saving.
- Added call status callback.
- Added recording callback.
- Added state recovery using both `CallSid` and caller phone number.

### Appointment Service

```text
app/services/appointment_service.py
```

Added:

- doctor lookup by department
- doctor matching from speech
- date/time parsing
- slot availability check
- voice appointment creation

### Conversation Service

```text
app/services/conversation_service.py
```

Added:

- save conversation messages
- fetch conversation messages
- generate call transcript

### Call Service

```text
app/services/call_service.py
```

Added:

- create or fetch call log
- update call status
- save call recording URL

### Twilio Service

```text
app/services/twilio_service.py
```

Added:

- XML response helper
- Gather response helper
- final response helper
- safe AI conversation logging

### Appointment Model

```text
app/models/appointments.py
```

Added:

```text
doctor_name
```

### Call Models

```text
app/models/call_logs.py
app/models/call_recording.py
app/models/call_transcript.py
```

Added/fixed:

- `CallLog`
- `CallRecording`
- `CallConversation`
- `CallTranscript`

## Alembic / Migration Work

Alembic was fixed to import all models correctly.

Changed:

```text
alembic/env.py
```

It now imports:

```text
CallLog
CallRecording
CallConversation
CallTranscript
```

It also reads `DATABASE_URL` from app config.

### Migration Files

Call tracking migration:

```text
alembic/versions/91f7e164e5b2_add_call_tracking_tables.py
```

Repair migration:

```text
alembic/versions/b2d8f9a1c3e4_repair_call_tracking_schema.py
```

Doctor name migration:

```text
alembic/versions/c6a4d2e7f901_add_doctor_name_to_appointments.py
```

Run migrations with:

```bash
.venv/bin/alembic upgrade head
```

## Twilio Configuration

In Twilio Voice Configuration:

### A call comes in

```text
https://YOUR-NGROK-URL/voice
```

Method:

```text
HTTP POST
```

### Call status changes

```text
https://YOUR-NGROK-URL/call-status
```

Method:

```text
HTTP POST
```

### Recording status callback

Use if recording is enabled:

```text
https://YOUR-NGROK-URL/recording-status
```

Method:

```text
HTTP POST
```

## Environment Configuration

`.env` should include:

```text
DATABASE_URL=postgresql://doctoradmin:doctor1234@localhost/doctor
GROQ_API_KEY=your_groq_key
PUBLIC_BASE_URL=https://YOUR-NGROK-URL
```

Do not share real API keys publicly.

## How To Run

Start PostgreSQL.

Run migrations:

```bash
.venv/bin/alembic upgrade head
```

Start FastAPI:

```bash
uvicorn main:app --reload
```

Start ngrok:

```bash
ngrok http 8000
```

Update Twilio with the latest ngrok URL.

## Current Notes

- The voice conversation is working through Twilio.
- State is stored in memory using `conversation_state`.
- State is keyed by both `CallSid` and caller number to avoid losing state during Twilio callback/retry behavior.
- For production, in-memory state should eventually move to Redis or PostgreSQL.
- Conversation saving is best-effort so Twilio calls do not crash if logging tables have an issue.
- If call logs or conversations do not save, terminal output will show messages like:

  ```text
  CALL LOG SAVE FAILED
  USER CONVERSATION SAVE FAILED
  AI CONVERSATION SAVE FAILED
  ```

## Latest Working Booking Flow

Example:

```text
AI: Welcome to Akashwani Hospital. Please tell me your health issue.
User: I have skin allergy.
AI: You should consult the Dermatology department. Available doctors are: Dr. Priya Mehta. Which doctor would you prefer?
User: Dr Priya Mehta.
AI: Please tell me your full name.
User: Joy.
AI: I heard your name as Joy. I spell it as J, O, Y. Is this correct?
User: Yes.
AI: Please tell me your preferred appointment date and time.
User: Tomorrow at 5 PM.
AI: Doctor is available. Do you want to confirm your appointment with Doctor Dr. Priya Mehta on Tuesday, 09 June 2026 at 05:00 PM?
User: Yes.
AI: Your appointment has been booked successfully.
```
