from AoE2ScenarioParser.aoe2_scenario import AoE2Scenario
from AoE2ScenarioParser.datasets.conditions import Condition
from AoE2ScenarioParser.datasets.effects import Effect
from AoE2ScenarioParser.datasets.players import Player
from AoE2ScenarioParser.datasets.units import Unit
from AoE2ScenarioParser.datasets.terrains import Terrain
from AoE2ScenarioParser.datasets.buildings import Building
from AoE2ScenarioParser.datasets.trigger_lists import Attribute
from AoE2ScenarioParser.helper import helper
import random
import argparse

input_path = "./BughouseTestMap.aoe2scenario"
output_path = "./BughouseTestMapPost.aoe2scenario"

MAX_X=119
MAX_Y=119

MAX_UNITS_OF_TYPE = 200
MAX_SIMULTANEOUS_UNITS = 40

PLAYER1_TC_X = 20
PLAYER1_TC_Y = 20

PLAYER2_TC_X = 80
PLAYER2_TC_Y = 80

SCORCHED_TERRAIN_RADIUS=4
TC_WIGGLE_FACTOR=2

SCORCHED_TERRAIN_ID=Terrain.ROCK_1

GROUP_LIST = [
             [4, Unit.VILLAGER_FEMALE],#villager group
             [47, Unit.SCOUT_CAVALRY],#Scout cavalry group
             [6, Unit.MILITIA],#infantry group
             [0, Unit.ARCHER],#Archer group
             [36, Unit.CAVALRY_ARCHER],#Cavalry archer group
             [44, Unit.HAND_CANNONEER],#Handcannoneer group
             [12, Unit.KNIGHT],#Cavalry Group
             [13, Unit.MANGONEL],#Siege group
             [55, Unit.SCORPION],#Scorpion group
             [23, Unit.CONQUISTADOR],#Conq group
             [54, Unit.TREBUCHET_PACKED],#unpacked treb
             [51, Unit.TREBUCHET_PACKED],#Packed treb
             [35, Unit.PETARD],#Petard Group
             [18, Unit.MONK],#monk group
             [43, Unit.MONK],#monk with relic group
             ]

UNIT_LIST = [
             #Unit.VILLAGER_MALE, #Cant get villagers to be consistent
             #Unit.VILLAGER_FEMALE,
             Unit.ARCHER,
             Unit.SCOUT_CAVALRY,
             Unit.MILITIA,
             Unit.MAN_AT_ARMS,
             Unit.SKIRMISHER,
             Unit.SPEARMAN,
             Unit.EAGLE_SCOUT,
             ]

PLAYER_LIST = [ 
                [Player.TWO, Player.ONE, PLAYER1_TC_X, PLAYER1_TC_Y],
                [Player.ONE, Player.TWO, PLAYER2_TC_X, PLAYER2_TC_Y]
                ]

STAGGER_LIST = []

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Add bughouse to a scenario")
  parser.add_argument("input", help="Input scenario file")
  parser.add_argument("output", help="Output scenario file")
  args = parser.parse_args()

  input_path = args.input
  output_path = args.output

  scenario = AoE2Scenario.from_file(input_path)
  trigger_manager = scenario.trigger_manager
  previous_trigger_id = None

  #get player starting TC's
  unit_manager = scenario.unit_manager
  for units in unit_manager.units:
    for unit in units:
      if unit.unit_const == Building.TOWN_CENTER:
        #one indexed zzzz
        PLAYER_LIST[unit.player.value-1][2] = int(unit.x) - SCORCHED_TERRAIN_RADIUS - TC_WIGGLE_FACTOR
        PLAYER_LIST[unit.player.value-1][3] = int(unit.y) - SCORCHED_TERRAIN_RADIUS - TC_WIGGLE_FACTOR
      
  
  #create unbuildable ground around spawn area
  map_manager = scenario.map_manager
  map_size = map_manager.map_size
  MAX_X = map_manager.map_width - 1
  MAX_Y = map_manager.map_height - 1
  for i in range(len(map_manager.terrain)):
    terrain_y, terrain_x = helper.i_to_xy(i, map_size) #backwards for some reason????
    for player in PLAYER_LIST:
      if abs(terrain_x - player[2]) <= SCORCHED_TERRAIN_RADIUS and abs(terrain_y - player[3]) <= SCORCHED_TERRAIN_RADIUS:
        map_manager.terrain[i].terrain_id = SCORCHED_TERRAIN_ID

  #build StaggerList
  for i in range(-SCORCHED_TERRAIN_RADIUS, SCORCHED_TERRAIN_RADIUS):
    for j in range(-SCORCHED_TERRAIN_RADIUS, SCORCHED_TERRAIN_RADIUS):
      STAGGER_LIST.append((i,j))

  #shuffle list
  random.shuffle(STAGGER_LIST)



  for player in PLAYER_LIST:
    for group in GROUP_LIST:
      trigger_list = []
      for i in range(MAX_UNITS_OF_TYPE):
        #create trigger
        trigger = trigger_manager.add_trigger(str(group[0]) + "_" + str(player[0]) + "_" + str(i))
        trigger_id = trigger.trigger_id
        trigger.looping=1
        trigger.enabled=0
        #trigger.add_condition(
        #    Condition.OWN_OBJECTS,
        #    amount_or_quantity=i,
        #    source_player=player[0],
        #    object_group=group[0])
        trigger.add_condition(
            Condition.OWN_FEWER_OBJECTS,
            amount_or_quantity=i,
            area_1_x=0,
            area_1_y=0,
            area_2_x=MAX_X,
            area_2_y=MAX_Y,
            source_player=player[0],
            object_group=group[0])
        trigger.add_effect(
            Effect.CREATE_OBJECT,
            object_list_unit_id=group[1],
            source_player=player[1],
            location_x=player[2] + STAGGER_LIST[(i+group[1].value)%len(STAGGER_LIST)][0],
            location_y=player[3] + STAGGER_LIST[(i+group[1].value)%len(STAGGER_LIST)][1],
            facet=-1)
        #Deactivate Self after success
        trigger.add_effect( 
            Effect.DEACTIVATE_TRIGGER,
            trigger_id=trigger_id)
        
        trigger2 = trigger_manager.add_trigger(str(group[0]) + "_" + str(player[0]) + "_OWN_" + str(i))
        trigger2.looping=1
        trigger2.enabled=1
        trigger2.add_condition(
            Condition.OWN_OBJECTS,
            amount_or_quantity=i+1,
            source_player=player[0],
            object_group=group[0])
        #trigger2.add_condition(
        #    Condition.OWN_FEWER_OBJECTS,
        #    amount_or_quantity=i+1,
        #    area_1_x=0,
        #    area_1_y=0,
        #    area_2_x=MAX_X,
        #    area_2_y=MAX_Y,
        #    source_player=player[0],
        #    object_group=group[0])
        #Activate main trigger
        trigger2.add_effect( 
            Effect.DEACTIVATE_TRIGGER,
            trigger_id=trigger2.trigger_id)
        trigger2.add_effect( 
            Effect.ACTIVATE_TRIGGER,
            trigger_id=trigger_id)

        #activate trigger 2 after trigger 1
        trigger.add_effect( 
            Effect.ACTIVATE_TRIGGER,
            trigger_id=trigger2.trigger_id)

        for id in trigger_list[-MAX_SIMULTANEOUS_UNITS:]:
          trigger2.add_effect( 
              Effect.ACTIVATE_TRIGGER,
              trigger_id=id)
          
        trigger_list.append(trigger.trigger_id)

  scenario.write_to_file(output_path, log_reconstructing=True)

