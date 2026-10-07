# YAML สำหรับลองส่งผ่าน Webex

ไฟล์ `02`–`10` ตรงกับตัวอย่างข้อ 2–10 ใน README ของ Student Starter ให้ @mention bot ของตนจริงและแนบ **หนึ่งไฟล์ต่อหนึ่งข้อความ** ตามลำดับ ข้อ 1 เป็นการส่งข้อความโดยไม่แนบ YAML จึงไม่มีไฟล์ในชุดนี้

ไฟล์ข้อ 3–10 เป็น **แม่แบบที่ยังส่งไม่ได้**: ดาวน์โหลดแล้วแทน `<assigned-router-ip>` ด้วย router ที่ได้รับมอบหมายในช่วง `10.0.29.102`–`10.0.29.105`, แทน `<student-id>` ด้วยรหัสของตนทั้งใน `name` และ `description`, และแทน `<unused-ipv4>` ด้วย IPv4 ที่เลือกใช้และยังไม่ซ้ำบน router โดยคง `/32` ไว้ ใช้ค่าเดียวกันในทุกไฟล์เพื่อให้ข้อ 3–10 ต่อเนื่องกัน ห้ามใช้ช่วง `192.0.2.128/27` ที่สงวนไว้สำหรับ Live test และห้าม `apply` หรือ `delete` interface ของผู้อื่น ไฟล์ `02-invalid-yaml.yaml` เสียโดยตั้งใจเพื่อทดสอบ `invalid_yaml`

นี่คือชุด **ลองส่งด้วยมือ** ไม่ถูก pytest เก็บอัตโนมัติ ผลของ `status`, `plan` และ `delete` ขึ้นกับสถานะ router ตอนส่ง: ข้อ 3/6 ใช้คำขอ status ประเภทเดียวกัน ข้อ 4/7 ใช้ plan เดียวกัน และข้อ 9/10 ส่ง delete ซ้ำหลังสถานะเปลี่ยน

Public tests ที่เกี่ยวข้องอยู่ใน `sample-tests/part1`–`part3`:

| ข้อ | Public case ที่ตรวจพฤติกรรมเดียวกัน |
|---|---|
| 2 | [invalid YAML](../part1/cases/05-invalid-yaml.yaml) |
| 3 | [RESTCONF not found](../part3/restconf/cases/02-not-found.yaml) |
| 4 | [plan create](../part2/cases/01-create.yaml) |
| 5 | [RESTCONF apply create](../part3/restconf/cases/05-apply-create.yaml) |
| 6 | [RESTCONF found](../part3/restconf/cases/01-found.yaml) |
| 7 | [plan no change](../part2/cases/04-no-change.yaml) |
| 8 | [invalid action](../part1/cases/11-restconf-delete-invalid-action.yaml) |
| 9 | [Netmiko delete existing](../part3/netmiko-textfsm/cases/07-delete-existing.yaml) |
| 10 | [Netmiko delete not found](../part3/netmiko-textfsm/cases/08-delete-not-found.yaml) |

ไฟล์ `cases/` ระบุผลที่คาดหวังและอ้างถึง `fixtures/` สำหรับ pytest; ไฟล์ในโฟลเดอร์นี้เป็นคำขอ YAML เต็มสำหรับแนบส่ง Webex
