"""Offline audit of saved numeric-tree choices and independent physics replay.

Reads original episode artifacts without editing them. Never imports a Jev client,
loads credentials, calls a model, or computes replacement controls.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')

from collections import Counter
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import time

import gymnasium as gym
import numpy as np

HERE = Path(__file__).resolve().parent
NAMES = ('steering', 'signed_acceleration')
HOLD = 10
FPS = 50


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def physics_telemetry(game, previous):
    """Recompute the recorded telemetry from fresh replay physics state."""
    hull = game.car.hull
    location = np.asarray(hull.position, dtype=float)
    centerline = np.asarray([(tile[2], tile[3]) for tile in game.track])
    segment = np.roll(centerline, -1, axis=0) - centerline
    fraction = np.clip(np.sum((location-centerline)*segment,axis=1)/np.sum(segment*segment,axis=1),0,1)
    projection = centerline+fraction[:,None]*segment
    nearest = int(np.argmin(np.linalg.norm(projection-location,axis=1)))
    forward = np.asarray(hull.GetWorldVector((0,1)))
    right = np.asarray(hull.GetWorldVector((1,0)))
    velocity = np.asarray(hull.linearVelocity)
    tangent = segment[nearest]/np.linalg.norm(segment[nearest])
    offset = projection[nearest]-location
    waypoints=[]
    for ahead in (2,4,8,12,16):
        delta=centerline[(nearest+ahead)%len(centerline)]-location
        f,r=float(delta@forward),float(delta@right)
        waypoints.append({'tiles_ahead':ahead,'forward':round(f,2),'right':round(r,2),'bearing_right_degrees':round(math.degrees(math.atan2(r,f)),2)})
    return {
        'speed':round(float(np.linalg.norm(velocity)),2),
        'forward_speed':round(float(velocity@forward),2),
        'rightward_slip_speed':round(float(velocity@right),2),
        'clockwise_yaw_rate_degrees_per_second':round(-math.degrees(hull.angularVelocity),2),
        'road_heading_right_degrees':round(math.degrees(math.atan2(tangent@right,tangent@forward)),2),
        'road_center_right_offset':round(float(offset@right),2),
        'distance_from_road_center':round(float(np.linalg.norm(offset)),2),
        'road_half_width':6.67,
        'wheels_touching_road':sum(bool(w.tiles) for w in game.car.wheels),
        'future_centerline_waypoints':waypoints,
        'previous_commands':dict(zip(NAMES,previous)),
    }


def history_entry(row):
    t=row['telemetry']
    return {
        'speed_before':t['speed'],
        'road_heading_right_degrees':t['road_heading_right_degrees'],
        'road_center_right_offset':t['road_center_right_offset'],
        'wheels_on_road':t['wheels_touching_road'],
        'steering_executed':row['command'][0],
        'signed_pedal_executed':row['command'][1],
    }


def expected_criteria(name, cuts, delta, is_final):
    value=lambda i: str(Decimal(-1)+delta*i)
    result={}
    for i in range(len(cuts)-1):
        lo=value(cuts[i])
        if is_final:
            number=Decimal(lo)
            if name=='signed_acceleration':
                effect=f'BRAKE {abs(number)}' if number<0 else f'THROTTLE {lo}' if number>0 else 'COAST; no throttle or brake; cannot start moving'
            else:
                effect='LEFT' if number<0 else 'RIGHT' if number>0 else 'STRAIGHT'
            result[str(i)]=f'Execute {name}={lo}: {effect}.'
        else:
            result[str(i)]=f'{lo} <= {name} < {value(cuts[i+1])}'
    return result


def audit_run(out):
    started=time.monotonic()
    immutable=[p for p in out.iterdir() if p.is_file() and p.suffix in ('.json','.jsonl','.npy','.py')]
    before_hashes={p.name:sha256(p) for p in immutable}
    summary=json.loads((out/'summary.json').read_text())
    rows=[json.loads(line) for line in (out/'actions.jsonl').read_text().splitlines()]
    records=json.loads((out/'api-records.json').read_text())
    assert len(rows)==summary['decision_count']
    assert len(records)==summary['api_calls']
    assert summary['executed_action_overrides']==0
    assert summary['no_new_tiles_guard'] is False
    assert summary['sim_time_limit_s']==180
    assert summary['history_controls']==6
    assert summary['gymnasium_version']==gym.__version__
    delta=Decimal(summary['resolution'])
    size=Decimal(2)/delta
    assert size==size.to_integral_value()
    branching=summary['branching']
    position=0
    decoded_actions=[]
    depth_counts=Counter()
    candidate_counts=Counter()
    stationary=0.0
    for index,row in enumerate(rows):
        assert row['step']==index*HOLD
        first_state=records[position]['request']['state']
        assert first_state['rules']==summary['policy_instructions']
        t=first_state['telemetry']
        assert {key:t[key] for key in row['telemetry']}==row['telemetry']
        assert set(t)==set(row['telemetry'])|{'stationary_duration_s','recent_controls_oldest_first'}
        stationary=stationary+0.2 if row['telemetry']['speed']<0.2 else 0.0
        assert t['stationary_duration_s']==round(stationary,2)
        expected_history=[history_entry(previous) for previous in rows[max(0,index-6):index]]
        assert t['recent_controls_oldest_first']==expected_history
        windows={name:(0,int(size)) for name in NAMES}
        layer=0
        while any(hi-lo>1 for lo,hi in windows.values()):
            record=records[position]
            request=record['request']
            response=record['response']
            assert request['model']==response['model']==summary['model']
            assert request['state']==first_state
            active={name for name,(lo,hi) in windows.items() if hi-lo>1}
            assert set(request['questions'])==set(response['answers'])==active
            for name in NAMES:
                if name not in active:
                    continue
                lo,hi=windows[name]
                count=min(branching,hi-lo)
                cuts=[lo+(hi-lo)*i//count for i in range(count+1)]
                assert len(set(cuts))==count+1
                question=request['questions'][name]
                assert question['type']=='choice'
                assert question['instructions'].startswith(summary['policy_instructions']+'\n\n')
                final=hi-lo<=branching
                criteria=expected_criteria(name,cuts,delta,final)
                assert question['criteria']==criteria
                expected_order=list(criteria)
                if summary['reverse_options']:
                    expected_order.reverse()
                assert list(question['criteria'])==expected_order
                assert ('These final options show exact controls that will be executed.' in question['instructions'])==final
                answer=response['answers'][name]
                assert answer['type']=='choice'
                assert answer['choice'] in criteria
                assert set(answer['probabilities'])==set(criteria)
                probabilities=list(answer['probabilities'].values())
                assert all(math.isfinite(p) and 0<=p<=1 for p in probabilities)
                assert abs(sum(probabilities)-1)<=len(probabilities)*0.005+0.001
                choice=int(answer['choice'])
                windows[name]=(cuts[choice],cuts[choice+1])
                candidate_counts[count]+=1
            saved_layer=row['trace'][layer]
            assert saved_layer['windows']=={name:list(window) for name,window in windows.items()}
            assert saved_layer['answers']==response['answers']
            position+=1
            layer+=1
        assert layer==len(row['trace'])
        depth_counts[layer]+=1
        decoded=[float(Decimal(-1)+delta*windows[name][0]) for name in NAMES]
        assert decoded==row['command']
        assert all(-1<=value<1 for value in decoded)
        decoded_actions.append(decoded)
    assert position==len(records)

    # Fresh environment, actual decoded API choices only, no policy or live API.
    env=gym.make('CarRacing-v3',continuous=True,max_episode_steps=9000)
    env.reset(seed=summary['seed'])
    game=env.unwrapped
    fresh_track=np.asarray([(tile[2],tile[3]) for tile in game.track])
    saved_track=np.load(out/'track.npy',allow_pickle=False)
    assert np.array_equal(fresh_track,saved_track)
    track_hash=hashlib.sha256(fresh_track.tobytes()).hexdigest()
    assert track_hash==summary['track_sha256']
    assert len(game.track)==summary['total_track_tiles']
    baseline=HERE.parents[1]/'car-racing-20260923'/f'geometry-reference-seed{summary["seed"]}'/'summary.json'
    baseline_hash=None
    if baseline.is_file():
        baseline_hash=json.loads(baseline.read_text())['track_sha256']
        assert baseline_hash==track_hash
    steps=0
    reward_total=0.0
    offroad=0
    previous=[0.0,0.0]
    terminated=truncated=False
    final_info={}
    max_reward_error=0.0
    try:
        for index,(row,action) in enumerate(zip(rows,decoded_actions)):
            assert not (terminated or truncated)
            actual_telemetry=physics_telemetry(game,previous)
            assert actual_telemetry==row['telemetry'], f'telemetry differs at decision {index}'
            steer,pedal=action
            physical=np.asarray([steer,max(pedal,0),max(-pedal,0)],dtype=np.float32)
            for _ in range(min(HOLD,summary['steps']-steps)):
                _,reward,terminated,truncated,final_info=env.step(physical)
                steps+=1
                reward_total+=float(reward)
                offroad+=int(not any(w.tiles for w in game.car.wheels))
                if terminated or truncated:
                    assert index==len(rows)-1 and steps==summary['steps']
                    break
            assert game.tile_visited_count==row['visited_tiles']
            reward_error=abs(reward_total-row['reward_total'])
            assert reward_error<1e-6
            max_reward_error=max(max_reward_error,reward_error)
            previous=action
        replay_reason='lap_finished' if final_info.get('lap_finished') else ('out_of_playfield' if terminated else 'time_limit')
        assert replay_reason==summary['stop_reason']
        assert summary['success']==bool(final_info.get('lap_finished'))
        assert bool(terminated or truncated)
        assert steps==summary['steps']
        assert reward_total==summary['reward']
        coverage=100*game.tile_visited_count/len(game.track)
        assert coverage==summary['coverage_percent']
        assert game.tile_visited_count==summary['visited_tiles']
        assert 100*offroad/steps==summary['fully_offroad_frame_percent']
        assert steps/FPS==summary['sim_seconds']
        result={
            'id':out.parent.name,'seed':summary['seed'],'branching':branching,'resolution':str(delta),
            'audit_passed':True,'independent_action_replay_verified':True,
            'decision_count':len(rows),'api_records_verified':len(records),'action_components_verified':len(rows)*2,
            'depth_distribution':dict(sorted(depth_counts.items())),
            'candidate_count_distribution_per_question':dict(sorted(candidate_counts.items())),
            'all_request_states_and_recorded_telemetry_verified':True,
            'all_replayed_current_telemetry_exactly_matches':True,
            'all_six_control_histories_and_stationary_duration_verified':True,
            'all_trace_windows_and_answers_verified':True,
            'all_options_labels_order_effects_and_probability_mass_verified':True,
            'executed_action_overrides':summary['executed_action_overrides'],
            'track_sha256':track_hash,'reference_track_hash_match':baseline_hash==track_hash if baseline_hash else None,
            'total_track_tiles':len(game.track),'visited_tiles':game.tile_visited_count,'coverage_percent':coverage,
            'reward':reward_total,'max_recorded_reward_error':max_reward_error,
            'steps':steps,'sim_seconds':steps/FPS,'fully_offroad_frame_percent':100*offroad/steps,
            'stop_reason':replay_reason,'terminated':bool(terminated),'truncated':bool(truncated),'lap_finished':bool(final_info.get('lap_finished')),
            'provider_reported_cost_usd':sum(record['response'].get('usage',{}).get('cost',0) for record in records),
            'original_artifact_sha256':before_hashes,
            'audit_wall_seconds':time.monotonic()-started,
        }
    finally:
        env.close()
    assert before_hashes=={p.name:sha256(p) for p in immutable}, 'Original artifacts changed during audit'
    result['original_artifacts_unchanged']=True
    print(json.dumps({key:result[key] for key in ('id','audit_passed','coverage_percent','reward','stop_reason','sim_seconds','depth_distribution','audit_wall_seconds')}),flush=True)
    return result


def main():
    paths=sorted(HERE.glob('K*/NumericJev-seed7'))
    assert len(paths)==4
    results=[audit_run(path) for path in paths]
    for name in ('runner-snapshot.py','decoder-snapshot.py','recovery-snapshot.py','comparison-snapshot.py'):
        assert len({r['original_artifact_sha256'][name] for r in results})==1
    assert len({r['track_sha256'] for r in results})==1
    output={
        'schema_version':1,'audit_passed':True,'gymnasium_version':gym.__version__,
        'method':'Independently reconstruct Decimal interval trees and all controls from saved Jev responses, verify complete request/trace/history, then replay only decoded controls in fresh seeded Gymnasium environments.',
        'network_or_live_api_calls':0,'original_records_modified':False,
        'source_snapshots_identical_across_four_conditions':True,'same_seed_track_identical_across_four_conditions':True,
        'runs':results,
        'totals':{'runs':len(results),'decisions':sum(r['decision_count'] for r in results),'api_records_verified':sum(r['api_records_verified'] for r in results),'action_components_verified':sum(r['action_components_verified'] for r in results),'physics_steps_replayed':sum(r['steps'] for r in results)},
        'limitations':'This verifies trace integrity and deterministic replay, not model accuracy, driving optimality, or generalization beyond this seed.',
    }
    (HERE/'verification.json').write_text(json.dumps(output,indent=2))
    print('AUDIT PASS '+json.dumps(output['totals']),flush=True)


if __name__=='__main__':
    main()
