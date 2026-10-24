#!/usr/bin/env python3
"""Generate the SRDF self-collision matrix with MuJoCo instead of moveit_setup_assistant.

  python3 generate_collision_matrix.py <unbolt.urdf> <scene.xml> <srdf.base> <srdf.out> [samples]

Link pairs are classified like the MoveIt Setup Assistant does:
  Adjacent  directly connected in the URDF tree (through geometry-less links)
  Default   in collision at the default (zero, clipped to limits) state
  Always    in collision in >= 95 % of random states
  Never     never in collision in any random state
Distances come from mujoco.mj_geomDistance on the MJCF collision geoms (convex hulls
of the OpenArm collision meshes). A hull contains its mesh, so a pair whose hulls
never touch cannot touch with the URDF meshes either: "Never" is conservative.
(collisions_updater hangs on this robot on ROS 2 Humble, hence this script.)
"""

import sys
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

urdf_path, mjcf_path, base_path, out_path = sys.argv[1:5]
samples = int(sys.argv[5]) if len(sys.argv) > 5 else 3000

# ---- URDF: links with collision geometry, tree, joint limits
urdf = ET.parse(urdf_path).getroot()
coll_links = [l.get('name') for l in urdf.findall('link') if l.find('collision') is not None]
parent_of = {j.find('child').get('link'): j.find('parent').get('link') for j in urdf.findall('joint')}


def geometric_parent(link):
    p = parent_of.get(link)
    while p is not None and p not in coll_links:
        p = parent_of.get(p)
    return p


adjacent = {frozenset((l, geometric_parent(l))) for l in coll_links if geometric_parent(l)}

# ---- MuJoCo: map collision geoms to URDF links
m = mujoco.MjModel.from_xml_path(mjcf_path)
d = mujoco.MjData(m)
BODY_TO_LINK = {f'openarm_{s}_ee_inner_finger': f'openarm_{s}_ee_link1' for s in ('left', 'right')}
BODY_TO_LINK.update({f'openarm_{s}_ee_outer_finger': f'openarm_{s}_ee_link2' for s in ('left', 'right')})
GEOM_TO_LINK = {'pedestal_collision': 'openarm_body_link0', 'chassis_collision': 'base_link'}
link_geoms = {}
for g in range(m.ngeom):
    if m.geom_contype[g] == 0 and m.geom_conaffinity[g] == 0:
        continue  # visual only
    name = m.geom(g).name
    body = m.body(m.geom_bodyid[g]).name
    link = GEOM_TO_LINK.get(name) or BODY_TO_LINK.get(body, body)
    if link in coll_links:
        link_geoms.setdefault(link, []).append(g)
missing = [l for l in coll_links if l not in link_geoms]
if missing:
    print('warning: URDF links without matching MuJoCo geoms (left enabled):', missing)

links = sorted(link_geoms)
pairs = [(a, b) for i, a in enumerate(links) for b in links[i + 1:] if frozenset((a, b)) not in adjacent]

# ---- joint sampling (arms + fingers; the base and wheels do not change self-collision)
arm_joints = [j for j in range(m.njnt) if m.joint(j).name.startswith('openarm_')]
mimic = {f'openarm_{s}_finger_joint2': f'openarm_{s}_finger_joint1' for s in ('left', 'right')}
fromto = np.zeros(6)


def set_state(q):
    for j, v in q.items():
        d.qpos[m.jnt_qposadr[j]] = v
    for follower, leader in mimic.items():
        d.qpos[m.joint(follower).qposadr[0]] = d.qpos[m.joint(leader).qposadr[0]]
    mujoco.mj_kinematics(m, d)  # also updates geom poses


def colliding(a, b):
    for ga in link_geoms[a]:
        for gb in link_geoms[b]:
            if mujoco.mj_geomDistance(m, d, ga, gb, 0.01, fromto) <= 0.0:
                return True
    return False


rng = np.random.default_rng(0)
default_q = {j: float(np.clip(0.0, *m.jnt_range[j])) for j in arm_joints}
set_state(default_q)
default_hits = {p for p in pairs if colliding(*p)}

hits = dict.fromkeys(pairs, 0)
for s in range(samples):
    set_state({j: rng.uniform(*m.jnt_range[j]) for j in arm_joints})
    for p in pairs:
        if p not in default_hits and colliding(*p):
            hits[p] += 1
    if (s + 1) % 500 == 0:
        print(f'  {s + 1}/{samples} samples')

reasons = {tuple(sorted(p)): 'Adjacent' for p in map(tuple, adjacent) if all(x in link_geoms for x in p)}
for p in pairs:
    if p in default_hits:
        reasons[p] = 'Default'
    elif hits[p] >= 0.95 * samples:
        reasons[p] = 'Always'
    elif hits[p] == 0:
        reasons[p] = 'Never'

# ---- write SRDF = base + disable_collisions
tree = ET.parse(base_path)
robot = tree.getroot()
for (a, b), why in sorted(reasons.items()):
    ET.SubElement(robot, 'disable_collisions', link1=a, link2=b, reason=why)
ET.indent(tree, space='  ')
tree.write(out_path, encoding='UTF-8', xml_declaration=True)

counts = {r: list(reasons.values()).count(r) for r in ('Adjacent', 'Default', 'Always', 'Never')}
enabled = len(pairs) - sum(1 for p in pairs if p in reasons)
print(f'{len(links)} links, {samples} samples: disabled {counts}, still checked {enabled} pairs')
print('checked pairs:', sorted(f'{a}<->{b}' for a, b in pairs if (a, b) not in reasons))
