# IPA2026 Final Exam — Student Starter

## เป้าหมายของงาน

สร้าง Webex bot ที่รับการ @mention พร้อมไฟล์ YAML **หนึ่งไฟล์ในข้อความเดียวกัน** ตรวจคำขอ ทำงานกับ router และตอบผลเป็น JSON **ในห้องที่ได้รับข้อความ** โปรแกรมต้องรองรับ `status`, `plan`, `apply`, `delete` ตาม backend ที่กำหนด

Starter นี้ยังไม่มีคำตอบ จุด `TODO` เป็นคอมเมนต์บอกงาน, `pass` เป็นโค้ดว่าง และ `raise NotImplementedError` ทำให้ฟังก์ชันหยุดเมื่อถูกเรียก **ให้เขียนฟังก์ชันเหล่านี้ใน `app/`** ตามข้อกำหนดใน `specs/` ซึ่งอยู่ใน repo เดียวกัน

## ใน repo มีอะไรบ้าง

| ที่อยู่ | ใช้ทำอะไร | นักศึกษาต้องทำอะไร |
|---|---|---|
| `app/` | โค้ดหลักสำหรับอ่าน YAML, วางแผน, ติดต่อ router และตอบ Webex | **เขียนฟังก์ชันที่ยังไม่เสร็จ** |
| `app/backends/` | โค้ด RESTCONF, NETCONF, Ansible และ Netmiko/TextFSM | เขียน backend ตามความสามารถที่กำหนด |
| `ansible/` | playbook และ inventory ที่เกี่ยวกับ Ansible | ทำให้ backend Ansible ใช้งานได้ตาม spec |
| `specs/` | ข้อกำหนดของ input, output, backend, Webex และการตรวจ | อ่านเป็นเกณฑ์หลักก่อนเขียนแต่ละส่วน |
| `tests/` | **โปรแกรม Python สำหรับรันทดสอบ** | รันให้ผ่าน **ไม่ควรแก้ tests ที่ให้มา** |
| `sample-tests/` | ข้อมูลตัวอย่าง: cases, fixtures และ YAML สำหรับลอง Live | อ่านตัวอย่างและเพิ่ม cases/fixtures ของตนได้ |
| `requirements.txt` | Python packages ที่ต้องติดตั้ง | ใช้ติดตั้ง dependencies |
| `README.md` | ภาพรวมและลำดับการทำงาน | เริ่มอ่านจากไฟล์นี้ |

Starter **ยังไม่มี** `Dockerfile`, `compose.yaml` และ `.github/workflows/student-ci.yaml` นักศึกษาต้องสร้างสามส่วนนี้เองใน Part 4

## งานแต่ละส่วน

| ส่วน | งานและไฟล์หลัก | Spec หลัก | คะแนน CI |
|---|---|---|---:|
| Part 1 | ตรวจ mention และ YAML: `app/core.py`, `app/request_handler.py` | `desired-state-spec-v1.md`, `response-spec-v1.md` | 2 |
| Part 2 | วางแผน `create/update/no_change`: `app/planner.py` | `plan-spec-v1.md` | 2 |
| Part 3 | เชื่อม router: `app/backends/` | `backend-spec-v1.md` | 4 |
| Part 4 | เชื่อมส่วนต่าง ๆ, Webex และ Docker: `app/dispatcher.py`, `app/integration.py`, `app/webex_client.py`, `app/webhook_server.py` | `integration-spec-v1.md`, `live-test-part4.md` | 2 |

ชื่อ spec ในตารางอยู่ใต้ `specs/` ทั้งหมด RESTCONF และ NETCONF รองรับ status/plan/apply; Ansible รองรับ apply; Netmiko/TextFSM รองรับ status/delete

## รูปแบบ YAML และความต่างของคำสั่ง

YAML หนึ่งไฟล์คือ **หนึ่งคำขอที่สมบูรณ์ในตัวเอง** มี `version`, `router`, `method`, `action` และ `desired.interface` โปรแกรมต้องอ่านไฟล์ ตรวจรูปแบบและตรวจว่า backend รองรับ action นั้น ก่อนทำงานกับ router

ตัวอย่างนี้ใช้รหัสสมมติ `66070123` และ interface เดียวกันเพื่อให้เห็นลำดับการทำงาน **ก่อนทดลองจริงให้เปลี่ยน router, interface และ IP เป็นค่าที่ตนได้รับมอบหมาย**

```yaml
version: 1
router: 10.0.29.101
method: restconf
action: status
desired:
  interface:
    name: Loopback66070123
    ipv4: 172.23.123.1/32
    description: IPA2026-66070123
    admin_state: up
```

| Action | ความหมาย | เปลี่ยน router หรือไม่ | ตัวอย่างผล |
|---|---|---|---|
| `status` | อ่านว่า interface มีอยู่หรือไม่ และค่าปัจจุบันคืออะไร | ไม่ | `found` หรือ `not_found` |
| `plan` | เทียบค่าปัจจุบันกับ `desired.interface` แล้วบอกว่าจะ `create`, `update` หรือ `no_change` | **ไม่** | `planned` พร้อม `operation` และ `changes` |
| `apply` | ทำให้ interface บน router มีค่าตาม `desired.interface` | **เปลี่ยนจริง** | `applied` |
| `delete` | ลบ interface ตามชื่อที่ระบุ | **เปลี่ยนจริง** | `deleted`; ถ้าลบซ้ำได้ `not_found` |

ลองใช้ไฟล์ตัวอย่างด้านบนโดยเปลี่ยนเฉพาะ `action` ตามลำดับ:

1. `action: status` — ถ้า interface ยังไม่มี ควรได้ `{"status":"ok","result":"not_found","interface":null}` คำว่า `not_found` ในกรณีนี้ **ไม่ใช่ error**
2. `action: plan` — ควรได้ `result: planned`, `operation: create` และ `changes` ที่อธิบายค่าที่จะเพิ่ม **router ยังไม่เปลี่ยน**
3. `action: apply` — ควรได้ `{"status":"ok","result":"applied"}` และ router ถูกเปลี่ยนจริง
4. ส่ง `status` อีกครั้ง — ควรได้ `result: found` พร้อม `interface` ที่มี IP, description และ admin state ตาม YAML
5. ส่ง `plan` อีกครั้ง — ควรได้ `operation: no_change` และ `changes: {}` เพราะค่าจริงตรงกับค่าที่ต้องการแล้ว

สำหรับ `delete` ต้องเปลี่ยน `method` เป็น `netmiko-textfsm` และระบุเพียงชื่อ interface:

```yaml
version: 1
router: 10.0.29.101
method: netmiko-textfsm
action: delete
desired:
  interface:
    name: Loopback66070123
```

การส่งครั้งแรกควรได้ `{"status":"ok","result":"deleted"}`; ส่งไฟล์เดิมซ้ำควรได้ `{"status":"ok","result":"not_found","interface":null}` ดูรูปแบบและข้อผิดพลาดทั้งหมดใน `specs/desired-state-spec-v1.md` และ `specs/response-spec-v1.md`

**ห้าม apply หรือ delete interface ของผู้อื่น** หาก `status` พบ interface ที่ไม่ใช่ของตน ให้หยุดก่อนทำขั้นตอนที่เปลี่ยน router

## ใช้ `tests/` และ `sample-tests/` อย่างไร

`tests/` คือ **โปรแกรมที่รันทดสอบ** ส่วน `sample-tests/` เป็น **ข้อมูลที่บางโปรแกรมใน `tests/` อ่าน** เช่น case ระบุ input และผลที่คาดหวัง ส่วน fixture เก็บข้อมูลที่ case ใช้

- นักศึกษา **ไม่ควรแก้โปรแกรมทดสอบที่ให้มาใน `tests/`** ให้แก้โค้ดใน `app/` จน tests ผ่าน
- โปรแกรมทดสอบบางไฟล์ของ Parts 1–3 ค้นหา `cases/*.yaml` อัตโนมัติ นักศึกษาเพิ่ม case พร้อม fixture ตามรูปแบบเดิมได้ **โดยไม่ต้องแก้ `tests/`**
- บาง tests เขียนกรณีไว้ใน Python โดยตรง ไม่ได้อ่าน `sample-tests/` ส่วน `sample-tests/part4/live/` เป็น YAML สำหรับส่งให้ Webex bot ด้วยมือ ไม่ถูก pytest เก็บอัตโนมัติ
- ตัวอย่าง: `tests/test_part1.py` อ่าน `sample-tests/part1/cases/`; `tests/test_part1_mentions.py` ตรวจ mention และกรณีไม่แนบไฟล์ที่เขียนไว้ใน Python โดยตรง
- การเพิ่มกรณีทดสอบช่วยตรวจงานของตน **ไม่เพิ่มคะแนนโดยตรง** เพราะการตรวจจริงใช้ tests และ cases ของผู้สอน

ติดตั้ง dependencies แล้วรัน public tests ซึ่งมี 82 กรณี:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q tests
```

การผ่าน public tests ยังไม่รับประกันว่าจะผ่าน hidden tests

## ลำดับการทำงาน

1. นำ Starter ไปสร้าง **GitHub repo งานของตนเอง** ทำงานบน branch `main` หาก repo เป็น private ต้องให้ผู้สอนอ่านได้
2. ทำ Parts 1–4 ตาม spec รัน public tests ระหว่างทำ
3. สร้าง `Dockerfile`, `compose.yaml` และ `.github/workflows/student-ci.yaml` เอง ให้ Student CI รัน public tests และ build Docker เมื่อ push `main` ไม่ต้อง publish image ไป Docker Hub
4. สร้าง Webex bot ของตน ตั้ง **ชื่อแสดงเป็นรหัสนักศึกษา 8 หลัก** เพิ่ม bot เข้าห้อง **IPA2026 ก่อนลงทะเบียน** แล้วเปิดโปรแกรม, webhook และ tunnel ให้พร้อมรับข้อความ
5. ลอง @mention bot ของตนพร้อม YAML หนึ่งไฟล์ ทดลอง `status → plan → apply → status → delete → delete ซ้ำ` บน **interface ที่ตนได้รับมอบหมายเท่านั้น** `plan` ไม่แก้ router; `apply` และ `delete` แก้สถานะจริง ดูตัวอย่าง YAML ใน `sample-tests/part4/live/` และขั้นตอนใน `specs/live-test-part4.md`
6. Push งานขึ้น `main` รอ Student CI ของ commit ล่าสุดผ่าน แล้วจึง `register → verify → grade → score`

## บัญชี Webex สองบัญชีของนักศึกษา

สมมตินักศึกษารหัส **66070123**:

| บัญชี | ใช้ทำอะไร |
|---|---|
| **บัญชีคน** `66070123@kmitl.ac.th` | นักศึกษาใช้พูดคุยใน Webex, ทดลองส่ง YAML ให้ bot ของตน และส่งคำสั่งตรวจให้ `IPA2026-Reference` |
| **บัญชี bot** ชื่อแสดง `66070123` | เป็นโปรแกรมที่นักศึกษาเขียน รับ YAML และตอบ JSON; ระบบผู้สอนจะส่ง Live test มาหา bot นี้ |

`IPA2026-Reference` เป็น **bot ผู้ตรวจของผู้สอน** ไม่ใช่ bot ที่นักศึกษาต้องเขียน ต้องเพิ่ม bot ของนักศึกษาเข้าห้อง IPA2026 ก่อน `register` และเปิด webhook/tunnel ไว้จนตรวจ Live เสร็จ

เวลา @mention ต้อง **เลือก bot จากรายการของ Webex จริง** การพิมพ์ `@ชื่อบอต` เป็นข้อความธรรมดาไม่พอ ถ้า mention bot นักศึกษาโดยไม่แนบ YAML ควรได้ `{"status":"error","result":"no_yaml"}`; ถ้าแนบมากกว่าหนึ่งไฟล์ควรได้ `{"status":"error","result":"multiple_attachments"}`

## Student CI, การตรวจ CI จริง และ Live

- **Student CI**: GitHub Actions ใน repo ของนักศึกษา ทำงานหลัง push `main` รัน public tests และ build Docker นักศึกษาดูผลและแก้เองก่อนส่งตรวจ
- **การตรวจ CI จริง**: เมื่อสั่ง `grade` ผู้สอนดึง **commit ล่าสุดของ `main`** ไปรัน public และ hidden tests รวม 131 กรณี พร้อมตรวจ Docker build คิดเป็น **10 คะแนน** ตามน้ำหนัก Parts 1–4 ในตาราง
- **Live test**: เมื่อ CI/build พร้อม ระบบส่ง YAML ผ่าน Webex ไปยัง bot นักศึกษา **ทีละกรณี 20 กรณี** ที่เลือกจากชุด 58 กรณี ตรวจทั้ง JSON ที่ตอบและสถานะจริงบน router คิดเป็น **10 คะแนน** กรณี `apply` ต้องเปลี่ยน router จริง; หลังตรวจระบบ cleanup interface ของการทดสอบ

Take-home เต็ม **20 คะแนน = CI 10 + Live 10** ส่วน MCQ อีก 10 คะแนนสอบและเก็บผลแยกนอกระบบนี้

## ตัวอย่างการส่งตรวจในห้อง IPA2026

ตัวอย่างนี้สมมติว่า **บัญชีคน** `66070123@kmitl.ac.th` เพิ่ม bot ชื่อ `66070123` เข้าห้องและเปิดใช้งานแล้ว งานอยู่ที่ `https://github.com/myname/ipa2026-work` ซึ่งเป็น **repo ของนักศึกษาเอง** ให้เปลี่ยน URL ตัวอย่างเป็น URL งานจริงของตน **ห้ามใช้ URL ของ Student Starter**

ให้บัญชีคนเลือก mention `@IPA2026-Reference` จาก Webex แล้วส่ง **ทีละข้อความ โดยไม่แนบ YAML** ข้อความตอบกลับด้านล่างเป็นตัวอย่างสมมติ; SHA, หมายเลขงาน และคะแนนจริงขึ้นกับงานที่ส่ง

### 1. `register` — ลงทะเบียน repo และ bot

ส่ง:

```text
@IPA2026-Reference register https://github.com/myname/ipa2026-work
```

ตัวอย่างผล:

```text
ลงทะเบียนสำเร็จ: 66070123
Repo: myname/ipa2026-work
ส่ง verify เพื่อตรวจความพร้อม, grade เพื่อตรวจ, หรือ score เพื่อดูคะแนน
การลงทะเบียนไม่ใช้โควตาและไม่รีเซ็ตคะแนน
```

### 2. `verify` — ตรวจความพร้อมฟรี

ส่ง:

```text
@IPA2026-Reference verify
```

ตัวอย่างผลเมื่อพร้อม:

```text
Verify 66070123: พร้อม
main SHA: 0123456789abcdef0123456789abcdef01234567
Student CI ที่ SHA นี้: ผ่าน
Live no-YAML smoke: ผ่าน
ไม่ใช้โควตา และไม่ได้รัน Live 20 กรณี
```

`verify` ตรวจ Student CI ของ **SHA ที่แสดง** และลองให้ bot ตอบแบบไม่แนบ YAML ไม่เริ่ม GitHub Actions ของผู้สอน ไม่ใช้โควตา และไม่บังคับ แต่ควรทำก่อน `grade`

### 3. `grade` — ส่งตรวจจริง **ได้สูงสุด 10 ครั้ง**

ส่ง:

```text
@IPA2026-Reference grade
```

ตัวอย่างผลเมื่อรับงาน:

```text
รับเข้าคิวตรวจ งาน #12
Commit: 0123456789abcdef0123456789abcdef01234567
66070123
ใช้สิทธิส่งตรวจ: 1/10 ครั้ง
ส่งตรวจได้อีก: 9 ครั้ง
คะแนน Take-home สูงสุด: ยังไม่มีงานที่ตรวจครบ
งานล่าสุด: เข้าคิว
จะแจ้งคะแนนอีกครั้งเมื่อตรวจเสร็จ
```

เมื่อตรวจเสร็จ ระบบส่งข้อความอีกครั้ง ตัวอย่างกรณีผ่านทั้งหมด:

```text
ตรวจเสร็จ — Build: ผ่าน
CI: 10/10
Live: 10/10
Take-home ครั้งนี้: 20/20
ใช้สิทธิส่งตรวจ: 1/10 ครั้ง
ส่งตรวจได้อีก: 9 ครั้ง
```

ผลจริงอาจได้คะแนนต่ำกว่าตัวอย่าง `grade` ที่รับเป็นงานใหม่ **ใช้โควตาหนึ่งครั้ง** แม้โค้ด, tests, build หรือ bot ของนักศึกษามีปัญหา

### 4. `score` — ดูผลฟรี

ส่ง:

```text
@IPA2026-Reference score
```

ตัวอย่างผลหลังตรวจเสร็จ:

```text
66070123
ใช้สิทธิส่งตรวจ: 1/10 ครั้ง
ส่งตรวจได้อีก: 9 ครั้ง
คะแนน Take-home สูงสุด: 20/20
งานล่าสุด: ตรวจเสร็จ
คะแนน CI ล่าสุด: 10/10
คะแนน Live ล่าสุด: 10/10
```

## โควตาและข้อควรระวัง

- `grade` ส่งตรวจจริงได้ **ไม่เกิน 10 ครั้ง**; `register`, `verify`, `score` ไม่ใช้โควตา
- หากแก้โค้ด ให้ push commit ใหม่และรอ Student CI ของ **commit ใหม่นั้น** ผ่านก่อน `grade` อีกครั้ง การสั่งตรวจ repo และ commit เดิมที่ตรวจเสร็จแล้วจะแสดงผลเดิม ไม่ใช้ครั้งใหม่
- ปัญหาของงานที่ส่ง เช่น tests/build ไม่ผ่าน, ใช้เวลานานเกินกำหนด หรือ bot ไม่ตอบ Live ใช้โควตา ความขัดข้องของระบบผู้สอน, GitHub, Webex หรือ router คืนโควตา
- คะแนนสูงสุดเลือกจาก **การส่งครั้งเดียว** ไม่ผสม CI และ Live จากต่างครั้ง
- ใช้ AI ช่วยทำ Take-home ได้ แต่ต้องตรวจผล เข้าใจและอธิบายโค้ดที่ส่งได้ด้วยตนเอง
- เก็บ `WEBEX_BOT_TOKEN`, `ROUTER_USER`, `ROUTER_PASS` ใน environment หรือ `.env` เท่านั้น **ห้าม commit `.env`, token หรือรหัสผ่าน**
