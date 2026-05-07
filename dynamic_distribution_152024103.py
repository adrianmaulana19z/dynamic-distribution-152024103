"""
=============================================================
  DYNAMIC DISTRIBUTION — NRP 152024103 (NRP Ganjil)
=============================================================
  Algoritma  : Least Connection with Dynamic Speed
  Tujuan     : Mendistribusikan tugas secara dinamis berdasarkan
               antrian terpendek + kecepatan server real-time,
               lalu menampilkan EXPECTED OPTIMAL TIME
               (prediksi waktu sistem menyelesaikan semua tugas).

  Pseudocode:
    1. Inisialisasi N server dengan base_speed & variance berbeda
    2. Untuk setiap tick (satuan waktu simulasi):
         a. Hasilkan batch tugas baru
         b. Assign tiap tugas ke server antrian TERPENDEK (Least Connection)
            - tiebreak: pilih server dengan base_speed tertinggi
         c. Setiap server proses tugas sesuai kecepatan DINAMIS saat ini
            (base_speed ± random variance → simulasi fluktuasi nyata)
         d. Hitung Expected Optimal Time = max(antrian / kecepatan) semua server
         e. Tampilkan status setiap CHECK_INTERVAL tick
    3. Hentikan saat semua antrian kosong → catat sebagai Optimal Time
    4. Ulangi simulasi dengan Round-Robin statis sebagai pembanding
=============================================================
"""

import random

random.seed(103)   # seed dari 3 digit akhir NRP → hasil reproducible

# ─────────────────────────────────────────────────────────────
#  KONFIGURASI SERVER
#  base_speed : tugas yang bisa diproses per tick (rata-rata)
#  variance   : ±fluktuasi kecepatan (simulasi kondisi jaringan/CPU)
# ─────────────────────────────────────────────────────────────
SERVERS = {
    "Node-Alpha":   {"base_speed": 4,  "variance": 3},   # sedang, sangat fluktuatif
    "Node-Beta":    {"base_speed": 2,  "variance": 1},   # lambat, stabil
    "Node-Gamma":   {"base_speed": 1,  "variance": 1},   # paling lambat
    "Node-Delta":   {"base_speed": 6,  "variance": 4},   # tercepat, tidak stabil
}

TOTAL_TASKS    = 120   # total tugas yang disimulasikan
TASKS_PER_TICK = 4     # tugas baru yang datang setiap tick (lebih kecil dari kapasitas)
CHECK_INTERVAL = 5     # cetak status setiap N tick

server_names = list(SERVERS.keys())


# ─────────────────────────────────────────────────────────────
#  FUNGSI-FUNGSI UTAMA
# ─────────────────────────────────────────────────────────────

def get_dynamic_speed(server: str) -> float:
    """
    Simulasi kecepatan server saat ini yang berfluktuasi.
    Kecepatan = base_speed + random(-variance, +variance)
    Minimal 0.5 task/tick agar server tidak pernah berhenti total.
    """
    cfg   = SERVERS[server]
    speed = cfg["base_speed"] + random.uniform(-cfg["variance"], cfg["variance"])
    return max(0.5, round(speed, 2))


def least_connection_assign(queue: dict) -> str:
    """
    Inti algoritma Dynamic Distribution:
    Pilih server dengan ANTRIAN TERPENDEK saat ini.
    Jika ada yang seri, pilih server dengan base_speed tertinggi.
    """
    min_q      = min(queue.values())
    candidates = [s for s, q in queue.items() if q == min_q]
    return max(candidates, key=lambda s: SERVERS[s]["base_speed"])


def round_robin_assign(index: int) -> str:
    """Round-Robin statis — baseline perbandingan tanpa optimasi dinamis."""
    return server_names[index % len(server_names)]


def expected_optimal_time(queue: dict, speed_snap: dict) -> float:
    """
    Hitung Expected Optimal Time dalam satuan tick.
    Rumus: max( antrian[s] / kecepatan[s] ) untuk semua server aktif.
    Ini adalah waktu tunggu server PALING SIBUK untuk selesai.
    """
    times = [
        queue[s] / speed_snap[s]
        for s in server_names
        if queue[s] > 0 and speed_snap.get(s, 0) > 0
    ]
    return round(max(times), 2) if times else 0.0


def print_status(queue, completed, speed_snap, tick, task_ptr):
    """Cetak tabel distribusi beban tiap server pada tick ini."""
    exp_t = expected_optimal_time(queue, speed_snap)
    total = sum(completed.values())
    print(f"\n  {'─'*68}")
    print(f"  Tick {tick:>3}  |  Terkirim: {task_ptr}/{TOTAL_TASKS}"
          f"  |  Selesai: {total}"
          f"  |  Exp. Optimal Time: {exp_t:.2f} tick")
    print(f"  {'─'*68}")
    print(f"  {'Server':<14} {'Antrian':>9} {'Selesai':>9} "
          f"{'Speed':>8} {'Est.Beres':>11}  Beban")
    print(f"  {'─'*64}")
    for s in server_names:
        spd = speed_snap.get(s, SERVERS[s]["base_speed"])
        est = round(queue[s] / spd, 2) if spd > 0 and queue[s] > 0 else 0.0
        bar = "█" * int(queue[s])
        print(f"  {s:<14} {queue[s]:>9.1f} {completed[s]:>9} "
              f"{spd:>7.2f}  {est:>9.2f}t  {bar}")


# ─────────────────────────────────────────────────────────────
#  SIMULASI 1 — DYNAMIC (Least Connection)
# ─────────────────────────────────────────────────────────────
print("=" * 70)
print("   DYNAMIC DISTRIBUTION  ·  NRP 152024103")
print("   Algoritma: Least Connection with Dynamic Speed")
print("=" * 70)
print(f"\n  {'Server':<14} {'Base Speed':>12} {'Variance':>10}  Karakteristik")
print(f"  {'─'*58}")
chars = ["Sedang, fluktuatif", "Lambat, stabil", "Paling lambat", "Tercepat, tidak stabil"]
for (s, cfg), ch in zip(SERVERS.items(), chars):
    print(f"  {s:<14} {cfg['base_speed']:>12} ±{cfg['variance']:>8}  {ch}")
print(f"\n  Total tugas : {TOTAL_TASKS}  |  Tugas/tick : {TASKS_PER_TICK}")
print(f"  Cek status  : setiap {CHECK_INTERVAL} tick\n")

queue_dyn     = {s: 0.0 for s in server_names}
completed_dyn = {s: 0   for s in server_names}
speed_log     = {s: []  for s in server_names}
speed_snap    = {}
task_ptr      = 0
tick          = 0
optimal_tick  = None
exp_time_log  = []

while True:
    tick += 1

    # (a) Kirim batch tugas baru → assign via Least Connection
    batch = min(TASKS_PER_TICK, TOTAL_TASKS - task_ptr)
    for _ in range(batch):
        chosen = least_connection_assign(queue_dyn)
        queue_dyn[chosen] += 1
        task_ptr += 1

    # (b) Setiap server proses tugas dengan kecepatan dinamis
    for s in server_names:
        spd = get_dynamic_speed(s)
        speed_snap[s] = spd
        speed_log[s].append(spd)
        processed       = min(queue_dyn[s], spd)
        queue_dyn[s]    = max(0.0, queue_dyn[s] - processed)
        completed_dyn[s] += int(processed + 0.5)

    # (c) Catat expected optimal time di setiap tick
    exp_t = expected_optimal_time(queue_dyn, speed_snap)
    exp_time_log.append((tick, exp_t))

    # (d) Cetak status berkala
    if tick % CHECK_INTERVAL == 0:
        print_status(queue_dyn, completed_dyn, speed_snap, tick, task_ptr)

    # (e) Cek kondisi selesai
    if task_ptr >= TOTAL_TASKS and all(q <= 0.1 for q in queue_dyn.values()):
        optimal_tick = tick
        if tick % CHECK_INTERVAL != 0:
            print_status(queue_dyn, completed_dyn, speed_snap, tick, task_ptr)
        print(f"\n  {'★'*60}")
        print(f"  ★★  EXPECTED OPTIMAL TIME TERCAPAI pada TICK ke-{optimal_tick}!  ★★")
        print(f"  {'★'*60}\n")
        break


# ─────────────────────────────────────────────────────────────
#  SIMULASI 2 — STATIC Round-Robin (baseline)
# ─────────────────────────────────────────────────────────────
random.seed(103)   # reset seed → kondisi kecepatan identik

queue_rr      = {s: 0.0 for s in server_names}
completed_rr  = {s: 0   for s in server_names}
task_ptr_rr   = 0
tick_rr       = 0
rr_idx        = 0

while True:
    tick_rr += 1
    batch = min(TASKS_PER_TICK, TOTAL_TASKS - task_ptr_rr)
    for _ in range(batch):
        chosen = round_robin_assign(rr_idx)
        queue_rr[chosen] += 1
        task_ptr_rr += 1
        rr_idx      += 1
    for s in server_names:
        spd = get_dynamic_speed(s)
        processed     = min(queue_rr[s], spd)
        queue_rr[s]   = max(0.0, queue_rr[s] - processed)
        completed_rr[s] += int(processed + 0.5)
    if task_ptr_rr >= TOTAL_TASKS and all(q <= 0.1 for q in queue_rr.values()):
        break


# ─────────────────────────────────────────────────────────────
#  KESIMPULAN & PERBANDINGAN
# ─────────────────────────────────────────────────────────────
improvement = (tick_rr - optimal_tick) / tick_rr * 100

print("=" * 70)
print("  PERBANDINGAN HASIL SIMULASI")
print("=" * 70)
print(f"\n  {'Metode':<40} {'Selesai di Tick':>15}")
print(f"  {'─'*57}")
print(f"  {'Dynamic  — Least Connection (Optimized)':<40} {optimal_tick:>15}")
print(f"  {'Static   — Round Robin (Baseline)':<40} {tick_rr:>15}")
print(f"\n  Peningkatan efisiensi : {improvement:.1f}% lebih cepat")

print(f"\n  Detail distribusi & performa server (Dynamic):")
print(f"  {'─'*57}")
for s in server_names:
    avg = sum(speed_log[s]) / len(speed_log[s])
    share = completed_dyn[s] / sum(completed_dyn.values()) * 100
    print(f"  {s:<14}  selesai {completed_dyn[s]:>3} tugas ({share:>4.1f}%)"
          f"  |  avg speed {avg:.2f} t/tick")

print(f"\n  Tren Expected Optimal Time (per {CHECK_INTERVAL} tick):")
print(f"  {'─'*57}")
for t, et in exp_time_log:
    if t % CHECK_INTERVAL == 0 or t == optimal_tick:
        bar = "▓" * int(et * 2)
        print(f"  Tick {t:>3}  →  {et:>6.2f} tick  {bar}")

print(f"\n  ✔  Expected Optimal Time  → Tick ke-{optimal_tick}")
print(f"  ✔  Dynamic Least Connection {improvement:.1f}% lebih cepat dari Round-Robin")
print("=" * 70)