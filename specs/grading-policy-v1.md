# Grading Policy

## Submission limit
Each student may submit up to 10 official grading attempts.
Local tests and local Docker builds are not limited.
A duplicate submission of the same repository and commit returns its
existing result without consuming another attempt.
An instructor infrastructure failure does not consume an attempt.
Student submission failures, including failing or timed-out official tests,
Docker build failures, and an unresponsive student bot, consume an attempt.
Only test results that completed and were recorded count toward CI points.

## Registration and Webex commands
IPA2026 is the student manual test room. Use only an assigned router in `10.0.29.102`–`10.0.29.105` there. Router `10.0.29.101` is reserved for official Live grading in IPA2026 Exam Room. Do not send manual YAML tests in the exam room. The student bot must receive mentions in both rooms and reply in the room of each request.

Use a Webex account whose email is `student-id@kmitl.ac.th`. Add one student bot
with an eight-digit student ID as its exact display name to both IPA2026 and IPA2026 Exam Room. Keep its webhook and tunnel available in both rooms for grading. Put the project and
`compose.yaml` at the repository root, and make the `main` branch readable to
the instructor (grant access if the repository is private).

In IPA2026 Exam Room, choose a real @mention of the IPA2026-Reference bot from Webex's
suggestions, then type one of these commands. A plain-text bot name is not a
mention. Students do not include their student ID in these commands:

- `register https://github.com/owner/repository`: record the repository and
  find exactly one room bot whose display name matches the student's ID.
- `verify`: check registration, the readable latest `main` SHA, successful
  Student CI for that exact SHA, and two smoke responses from the
  registered bot in the exam room: `no_yaml` without an attachment and
  `invalid_version` for a YAML attachment. The YAML has an invalid version
  and cannot change a router. This is optional, free, and does not start a GitHub Actions
  run or consume a grading attempt. Repeated checks have a 30-second cooldown.
  If Student CI has not passed, the live smoke is skipped. When other Webex
  commands are waiting, verify yields immediately so it does not hold their queue.
- `grade`: grade the latest `main` SHA using official CI/build, followed by
  Live only when the build succeeds and official tests finish.
- `score`: show the best Take-home score out of 20, latest result, and attempts used/remaining.
  This is free. Queued submissions also show their current queue position.

The instructor may use `queue` in IPA2026 Exam Room to see the
student IDs and submission numbers currently running in CI or Live, and those
waiting in each queue. This command does not consume an attempt.

## CI: 10 points
Public and hidden tests contribute within each part:
- Part 1: 2 points
- Part 2: 2 points
- Part 3: 4 points
- Part 4: 2 points

For each part:
points = passed tests / total tests in that part * part weight.

Student CI runs public tests, builds the webhook image, and performs an offline HTTP smoke check inside it.
Official instructor grading also runs hidden tests and its own image smoke check.
Docker Hub publication is not required.
The grading scheduler can have up to four official CI runs in progress. Live
testing remains one student at a time so router changes and Webex replies do
not overlap. All accepted submissions remain in the grading database while
they wait; being in the queue does not require the student to resubmit.
The official CI job has a five-minute limit. Official tests stop after two
minutes and Docker build stops after 90 seconds. A student code timeout is a
scored submission and Live is skipped. Grading service or GitHub failures
refund the attempt.

## Live: 10 points
The instructor maintains a pool of 58 Live input variants. Every submission
receives exactly 20 equally weighted cases, worth 0.5 points each: one selected
from each required capability group. The selection is reproducible for that
submission and the selected variant IDs are stored with its result. This keeps
coverage comparable while changing the YAML values and syntax between attempts.
Official build verification must succeed before live grading begins.
If the build or image smoke fails, retain earned CI points and award zero live points.
If the registered bot does not answer a Live request by its deadline, the
remaining Live cases fail immediately so the next student's turn can begin.
This consumes the attempt. A grading service, Webex API, or router failure
refunds the attempt.
Live coverage includes YAML validation, status found/not_found, plan
create/no_change/update, apply with independent router-state verification,
delete/repeated delete, and supported RESTCONF, NETCONF, Ansible, and
Netmiko/TextFSM operations.

Starting `grade` authorizes the runner to delete and recreate only
`Loopback<student-id>` on router `10.0.29.101`. It removes that interface
before Live even if manual testing left a different description, and removes
it again after Live. Other interface names are never cleaned up. The grade
acceptance message also tells the student about this reset.

Official Live /32 addresses come from `192.0.2.128/27`. Students must not
use this range for their own manual configurations. Student bots must still
accept Live requests from the grader using this range.

Deploy the bot using Docker Compose and keep it available for grading.
The instructor tests it through Webex mentions and YAML attachments.
Live requests and JSON replies are visible in IPA2026 Exam Room.
Sampling does not hide YAML attachments from other exam room members.
No screenshots, Docker command output, or manual live logs are submitted.

## Final score
The final exam uses CI 10 + Live 10 + MCQ 10 = 30 points. MCQ is a separate
assessment kept outside this grading system. During the MCQ assessment, the
only permitted reference is the IPA2026-student-starter repository, including
its README, specs, code, and public tests. The grading bot and
SQLite report only the Take-home CI + Live result out of 20. The instructor
combines MCQ points with Take-home points outside this system.
Use the highest Take-home total from a single valid grading attempt
submitted before the deadline.
Do not combine CI and live scores from different attempts.
Finish processing attempts accepted before the deadline.
Keep every attempt's repository, commit SHA, results and score.

## Bot feedback
On acceptance, report the attempt count, remaining attempts and previous best.
After grading, report CI score, live score, Take-home score, best Take-home score,
attempt count and remaining attempts.
A score query does not consume an attempt.
