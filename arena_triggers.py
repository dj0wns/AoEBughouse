from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.objects.managers.player_manager import spread_player_attributes
import random
import argparse
import math

PLAYER_COUNT = 8

GOLD_RADIUS = 5

GOLD_BIG_LENGTH = 5
GOLD_MEDIUM_LENGTH = 4
GOLD_SMALL_LENGTH = 3

GOLD_BIG_PER_PLAYER = 2
GOLD_MEDIUM_PER_PLAYER = 2
GOLD_SMALL_PER_PLAYER = 2

STONE_RADIUS = 4

STONE_BIG_LENGTH = 4
STONE_MEDIUM_LENGTH = 3

STONE_BIG_PER_PLAYER = 3
STONE_MEDIUM_PER_PLAYER = 2

VILLAGER_RADIUS = 1
VILLAGERS_PER_PLAYER = 3

SHEEP_PER_PLAYER = 10

DEER_PATCHES_PER_PLAYER = 8

BERRY_RADIUS = 5
BERRY_LENGTH = 5
BERRY_PATCHES_PER_PLAYER = 4

DEER_RADIUS = 3
DEER_PATCHES_PER_PLAYER = 3
DEER_PER_PATCH = 2

BOAR_RADIUS = 3
BOAR_PER_PLAYER = 4

SHEEP_RADIUS = 2
SHEEP_PER_PLAYER = 12

SMALL_FOREST_RADIUS = 10 #these are generated first so spread them out
SMALL_FOREST_SIZE = 6
SMALL_FORESTS_PER_PLAYER = 3

OUTER_FOREST_MULTIPLIER = 0.40
OUTER_FOREST_MULTIPLIER_INVERSE = (1 - 2*OUTER_FOREST_MULTIPLIER) / 2

HILL_LARGE_HEIGHT=4
HILL_LARGE_LENGTH=5
HILL_LARGE_PER_PLAYER=3

HILL_MEDIUM_HEIGHT=3
HILL_MEDIUM_LENGTH=10
HILL_MEDIUM_PER_PLAYER=4

HILL_SMALL_HEIGHT=2
HILL_SMALL_LENGTH=6
HILL_SMALL_PER_PLAYER=10

WALL_RADIUS=15
WALL_MODULUS=3

IDS_THAT_BLOCK=set([
  OtherInfo.GOLD_MINE.ID,
  OtherInfo.STONE_MINE.ID,
  OtherInfo.FORAGE_BUSH.ID,
  OtherInfo.FRUIT_BUSH.ID] + \
  [unit.ID for unit in OtherInfo.trees()])


#List of all triggers used for writing a disabling trigger later
PLAYER_TRIGGERS=[{'tc':[],'wall':[]},
                 {'tc':[],'wall':[]},
                 {'tc':[],'wall':[]},
                 {'tc':[],'wall':[]},
                 {'tc':[],'wall':[]},
                 {'tc':[],'wall':[]},
                 {'tc':[],'wall':[]},
                 {'tc':[],'wall':[]}]
#TODO rewrite all generate functions as a single function - would make it easier to alternate too(maybe go in a circle per player)

#Holds the set of empty tiles to increase radius lookup speed
EMPTY_TILES = set()

EMPTY_TOWN_CENTER_TILES = set()
TOWN_CENTERS = set()

def check_unit_square(unit_manager, x, y, radius):
  for c_x in range(x-radius, x+radius):
    for c_y in range(y-radius, y+radius):
      if (c_x,c_y) not in EMPTY_TILES:
        return True
  return False

def check_tile(unit_manager, x, y):
  if (x,y) not in EMPTY_TILES:
    return True
  return False

def check_tc_square(unit_manager, x, y):
  #1 tc per 2 tiles, range is not inclusive
  for c_x in range(x-1, x+1):
    for c_y in range(y-1, y+1):
      if (c_x,c_y) in TOWN_CENTERS:
        return True
  for c_x in range(x-2, x+2):
    for c_y in range(y-2, y+2):
      if (c_x,c_y) not in EMPTY_TOWN_CENTER_TILES:
        return True
  return False

def find_open_tiles_with_radius(unit_manager, radius, max_x, max_y):
  tiles = []
  print(f'Count in EMPTY_TILES: {len(EMPTY_TILES)}')
  for tile in EMPTY_TILES:
    if not check_unit_square(unit_manager, tile[0], tile[1], radius):
      tiles.append((tile[0],tile[1]))
  print(f'Found this many suitable spots: {len(tiles)}')
  return tiles

def add_unit_and_clear_radius_tiles(unit_manager, tiles, player_id, unit_id, x, y, radius):
  unit_manager.add_unit(player=player_id, unit_const=unit_id, x=x+0.5, y=y+0.5)
  #remove from EMPTY TILES
  EMPTY_TILES.remove((x,y))
  to_remove = set()
  for del_x in range(x-radius, x+radius):
    for del_y in range(y-radius, y+radius):
      to_remove.add((del_x,del_y))
  return to_remove

#assumes there is space! use the radius variable for this
def generate_random_contiguous_shape(x, y, length):
  shape = [(x,y)]
  position_x = x
  position_y = y
  for i in range(1, length):
    options  = []
    if (position_x+1, position_y) not in shape:
      options.append((position_x+1, position_y))
    if (position_x-1, position_y) not in shape:
      options.append((position_x-1, position_y))
    if (position_x, position_y+1) not in shape:
      options.append((position_x, position_y+1))
    if (position_x, position_y-1) not in shape:
      options.append((position_x, position_y-1))
    #we got stuck just exit out
    if (len(options) == 0):
      break
    index = random.randrange(0,len(options))
    shape.append(options[index])
    position_x = options[index][0]
    position_y = options[index][1]
  return shape

#assumes there is space! use the radius variable for this
def generate_circle_shape(x, y, radius):
  shape = []
  for c_x in range(x-radius, x+radius):
    for c_y in range(y-radius, y+radius):
      if math.dist([x, y],[c_x, c_y]) < radius:
        shape.append((c_x, c_y))
  return shape

def generate_hill_in_line(map_manager, height, count_per_obj, count_per_player):
  #generate obj
  tiles = list(EMPTY_TOWN_CENTER_TILES)
  for i in range(count_per_player * PLAYER_COUNT):
    if not len(tiles):
      print("Ran out of space!!!")
    index = random.randrange(0,len(tiles))
    x = tiles[index][0]
    y = tiles[index][1]
    shape = generate_random_contiguous_shape(x, y, count_per_obj)
    to_remove = set()
    for cell in shape:
      c_x = cell[0]
      c_y = cell[1]
      map_manager.set_elevation(height, x1=c_x, y1=c_y)
      for del_x in range(c_x-height+1, c_x+height-1):
        for del_y in range(c_y-height+1, c_y+height-1):
          to_remove.add((del_x,del_y))
    for tile in to_remove:
      if tile in tiles:
        EMPTY_TOWN_CENTER_TILES.remove(tile)
        tiles.remove(tile)

def generate_obj_in_line(unit_manager, max_x, max_y, count_per_obj, count_per_player, avoidance_radius, player_id, object_id):
  #generate obj
  tiles = find_open_tiles_with_radius(unit_manager, avoidance_radius, max_x, max_y)
  for i in range(count_per_player * PLAYER_COUNT):
    if not len(tiles):
      print("Ran out of space!!!")
    index = random.randrange(0,len(tiles))
    x = tiles[index][0]
    y = tiles[index][1]
    shape = generate_random_contiguous_shape(x, y, count_per_obj)
    to_remove = set()
    for cell in shape:
      to_remove = set.union(to_remove, add_unit_and_clear_radius_tiles(unit_manager, tiles, player_id, object_id, cell[0], cell[1], avoidance_radius))
    for tile in to_remove:
      if tile in tiles:
        tiles.remove(tile)

def generate_small_forests(unit_manager, map_manager, max_x, max_y):
  tiles = find_open_tiles_with_radius(unit_manager, SMALL_FOREST_RADIUS, max_x, max_y)
  for i in range(SMALL_FORESTS_PER_PLAYER * PLAYER_COUNT):
    if not len(tiles):
      print("Ran out of space!!!")
    index = random.randrange(0,len(tiles))
    forest_x = tiles[index][0]
    forest_y = tiles[index][1]
    forests = generate_circle_shape(forest_x, forest_y, SMALL_FOREST_SIZE)
    to_remove = set()
    for forest in forests:
      to_remove = set.union(to_remove, add_unit_and_clear_radius_tiles(unit_manager, tiles, PlayerId.GAIA, OtherInfo.TREE_OAK_AUTUMN.ID, forest[0], forest[1], SMALL_FOREST_RADIUS))
      #update tile to match
      tile = map_manager.get_tile(x=forest[0], y=forest[1])
      tile.terrain_id = TerrainId.FOREST_OAK
    for tile in to_remove:
      if tile in tiles:
        tiles.remove(tile)

def generate_villagers(unit_manager, max_x, max_y):
  tiles = find_open_tiles_with_radius(unit_manager, VILLAGER_RADIUS, max_x, max_y)
  for i in range(VILLAGERS_PER_PLAYER):
    for j in range(PLAYER_COUNT):
      if not len(tiles):
        print("Ran out of space!!!")
      index = random.randrange(0,len(tiles))
      vil_x = tiles[index][0]
      vil_y = tiles[index][1]
      to_remove = add_unit_and_clear_radius_tiles(unit_manager, tiles, j+1, UnitInfo.VILLAGER_MALE.ID, vil_x, vil_y, VILLAGER_RADIUS)
      for tile in to_remove:
        if tile in tiles:
          tiles.remove(tile)

def add_script_trigger(xs_manager):
  xs_manager.initialise_xs_trigger(insert_index=0)
  xs_manager.add_script(xs_file_path="./nomad_arena.xs")

def add_wall_triggers(trigger_manager, unit_manager, max_x, max_y):
  trigger_count = 0
  # build wall list as only places tcs can make walls
  wall_tiles = set()
  for tile in TOWN_CENTERS:
    # adjust the wall modulus
    t_x = tile[0] - (tile[0] % WALL_MODULUS)
    t_y = tile[1] - (tile[1] % WALL_MODULUS)
    for x in range(t_x - WALL_RADIUS, t_x + WALL_RADIUS):
      wall_tiles.add((x,t_y+WALL_RADIUS))
      wall_tiles.add((x,t_y-WALL_RADIUS))
    for y in range(t_y - WALL_RADIUS, t_y + WALL_RADIUS):
      wall_tiles.add((t_x+WALL_RADIUS, y))
      wall_tiles.add((t_x-WALL_RADIUS, y))

  for tile in wall_tiles:
    x = tile[0]
    y = tile[1]
    #if something already in square continue
    if check_tile(unit_manager, x, y):
      continue
    for i in range(PLAYER_COUNT):
      wall_trigger = trigger_manager.add_trigger(f'{x}_{y}_{i}_wall_trigger', looping=False, enabled=False)
      #need 4 conditions and tc has to be in all 4
      wall_trigger.new_condition.script_call(xs_function=f'void wall{x}_{y}_{i}(){{isWall({x},{y},{i});}}')
      wall_trigger.new_effect.create_object(source_player=i+1, #Zero is gaia
                                            object_list_unit_id=BuildingInfo.STONE_WALL.ID,
                                            location_x=x,
                                            location_y=y)

      trigger_count += 1
      PLAYER_TRIGGERS[i]['wall'].append(wall_trigger.trigger_id)
  print(f'Wall triggers created: {trigger_count}')

def add_towncenter_triggers(trigger_manager, max_x, max_y):
  trigger_count = 0
  for x in range(max_x):
    for y in range(max_y):
      #if something already in square continue
      if check_tc_square(unit_manager, x, y):
        continue
      for i in range(PLAYER_COUNT):
        tc_trigger = trigger_manager.add_trigger(f'{x}_{y}_{i}_tc_trigger', looping=False)
        #need 4 conditions and tc has to be in all 4
        tc_trigger.new_condition.objects_in_area(source_player=i+1, #zero is gaia
                                                 object_list=BuildingInfo.TOWN_CENTER.ID,
                                                 quantity=1,
                                                 area_x1=x-1,
                                                 area_y1=y-1,
                                                 area_x2=x,
                                                 area_y2=y)
        tc_trigger.new_effect.script_call(message=f'void set{x}_{y}_{i}(){{setWalls({x},{y},{i});}}')
        TOWN_CENTERS.add((x,y))
        trigger_count += 1
        PLAYER_TRIGGERS[i]['tc'].append(tc_trigger.trigger_id)
  print(f'TC Triggers created: {trigger_count}')

def add_disable_triggers(trigger_manager, max_x, max_y):
  trigger_count = 0
  for i in range(PLAYER_COUNT):
    disable_trigger = trigger_manager.add_trigger(f'P{i}_disable_trigger', looping=False)
    #need 4 conditions and tc has to be in all 4
    disable_trigger.new_condition.script_call(xs_function=f'bool player_dis_{i}(){{return(didPlayerBuildTC({i}));}}')
    for trigger_id in PLAYER_TRIGGERS[i]['tc']:
      disable_trigger.new_effect.deactivate_trigger(trigger_id=trigger_id)
    for trigger_id in PLAYER_TRIGGERS[i]['wall']:
      disable_trigger.new_effect.deactivate_trigger(trigger_id=trigger_id)
    #Also deactivate self
    disable_trigger.new_effect.deactivate_trigger(trigger_id=disable_trigger.trigger_id)

def add_enable_triggers(trigger_manager, max_x, max_y):
  #Wall triggers are disabled until the frame that the tc is built and then disabled again
  trigger_count = 0
  for i in range(PLAYER_COUNT):
    enable_trigger = trigger_manager.add_trigger(f'P{i}_enable_trigger', looping=False)
    #need 4 conditions and tc has to be in all 4
    enable_trigger.new_condition.script_call(xs_function=f'bool player_en_{i}(){{return(didPlayerCompleteTC({i}));}}')
    # Don't reenable tc triggers or it causes weird looping
    for trigger_id in PLAYER_TRIGGERS[i]['wall']:
      enable_trigger.new_effect.activate_trigger(trigger_id=trigger_id)
    #Also deactivate self
    enable_trigger.new_effect.deactivate_trigger(trigger_id=enable_trigger.trigger_id)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Add bughouse to a scenario")
  parser.add_argument("input", help="Input scenario file")
  parser.add_argument("output", help="Output scenario file")
  args = parser.parse_args()


  input_path = args.input
  output_path = args.output

  scenario = AoE2DEScenario.from_file(input_path)
  trigger_manager = scenario.trigger_manager
  previous_trigger_id = None
  #set constants

  unit_manager = scenario.unit_manager
  map_manager = scenario.map_manager
  xs_manager = scenario.xs_manager
  player_manager = scenario.player_manager
  map_size = map_manager.map_size
  MAX_X = map_manager.map_width
  MAX_Y = map_manager.map_height

  circle_radius = MAX_X * OUTER_FOREST_MULTIPLIER
  circle_center_x = MAX_X / 2.
  circle_center_y = MAX_Y / 2.

  # Starting defaults for each player
  for player in PlayerId.all():
    player_manager.players[player].wood = 475
    player_manager.players[player].food = 200
    player_manager.players[player].gold = 100
    player_manager.players[player].stone = 300

  print('INIT Empty Tiles')
  for x in range(MAX_X):
    for y in range(MAX_Y):
      EMPTY_TILES.add((x,y))

  print('Generating Outer Trees')
  #generate trees
  for x in range(MAX_X):
    for y in range(MAX_Y):
      if math.dist([x, y],[circle_center_x, circle_center_y]) > circle_radius:
        unit_manager.add_unit(player=PlayerId.GAIA, unit_const=OtherInfo.TREE_OAK_AUTUMN.ID, x=x+0.5, y=y+0.5)
        #update tile to match
        tile = map_manager.get_tile(x=x, y=y)
        tile.terrain_id = TerrainId.FOREST_OAK
        EMPTY_TILES.remove((x,y))

  print('Generating Small Forests')
  generate_small_forests(unit_manager, map_manager, MAX_X, MAX_Y)
  print('Generating Berries')
  generate_obj_in_line(unit_manager, MAX_X, MAX_Y, BERRY_LENGTH, BERRY_PATCHES_PER_PLAYER, BERRY_RADIUS, PlayerId.GAIA, OtherInfo.FORAGE_BUSH.ID)
  print('Generating Big Gold')
  generate_obj_in_line(unit_manager, MAX_X, MAX_Y, GOLD_BIG_LENGTH, GOLD_BIG_PER_PLAYER, GOLD_RADIUS, PlayerId.GAIA, OtherInfo.GOLD_MINE.ID)
  print('Generating Medium Gold')
  generate_obj_in_line(unit_manager, MAX_X, MAX_Y, GOLD_MEDIUM_LENGTH, GOLD_MEDIUM_PER_PLAYER, GOLD_RADIUS, PlayerId.GAIA, OtherInfo.GOLD_MINE.ID)
  print('Generating Small Gold')
  generate_obj_in_line(unit_manager, MAX_X, MAX_Y, GOLD_SMALL_LENGTH, GOLD_SMALL_PER_PLAYER, GOLD_RADIUS, PlayerId.GAIA, OtherInfo.GOLD_MINE.ID)
  print('Generating Big Stone')
  generate_obj_in_line(unit_manager, MAX_X, MAX_Y, STONE_BIG_LENGTH, STONE_BIG_PER_PLAYER, GOLD_RADIUS, PlayerId.GAIA, OtherInfo.STONE_MINE.ID)
  print('Generating Medium Stone')
  generate_obj_in_line(unit_manager, MAX_X, MAX_Y, STONE_MEDIUM_LENGTH, STONE_MEDIUM_PER_PLAYER, STONE_RADIUS, PlayerId.GAIA, OtherInfo.STONE_MINE.ID)
  print('Generating Script Trigger')
  add_script_trigger(xs_manager)

  # use empty town center tiles because some things (like hills) block tcs but nothing else
  EMPTY_TOWN_CENTER_TILES = EMPTY_TILES.copy()
  print(f'There are {len(EMPTY_TOWN_CENTER_TILES)} open tc tiles')
  print('Generating Big Hills')
  generate_hill_in_line(map_manager, HILL_LARGE_HEIGHT, HILL_LARGE_LENGTH, HILL_LARGE_PER_PLAYER)
  print(f'There are {len(EMPTY_TOWN_CENTER_TILES)} open tc tiles')
  print('Generating Medium Hills')
  generate_hill_in_line(map_manager, HILL_MEDIUM_HEIGHT, HILL_MEDIUM_LENGTH, HILL_MEDIUM_PER_PLAYER)
  print(f'There are {len(EMPTY_TOWN_CENTER_TILES)} open tc tiles')
  print('Generating Small Hills')
  generate_hill_in_line(map_manager, HILL_SMALL_HEIGHT, HILL_SMALL_LENGTH, HILL_SMALL_PER_PLAYER)
  print(f'There are {len(EMPTY_TOWN_CENTER_TILES)} open tc tiles')
  print('Generating Town Center triggers')
  add_towncenter_triggers(trigger_manager, MAX_X, MAX_Y)
  print('Generating Wall Triggers triggers')
  add_wall_triggers(trigger_manager, unit_manager, MAX_X, MAX_Y)
  print('Generating disable triggers')
  add_disable_triggers(trigger_manager, MAX_X, MAX_Y)
  print('Generating enable triggers')
  add_enable_triggers(trigger_manager, MAX_X, MAX_Y)
  # these objects are non blocking so add last
  print('Generating Deer')
  generate_obj_in_line(unit_manager, MAX_X, MAX_Y, DEER_PER_PATCH, DEER_PATCHES_PER_PLAYER, DEER_RADIUS, PlayerId.GAIA, UnitInfo.DEER.ID)
  print('Generating Boar')
  generate_obj_in_line(unit_manager, MAX_X, MAX_Y, 1, BOAR_PER_PLAYER, BOAR_RADIUS, PlayerId.GAIA, UnitInfo.WILD_BOAR.ID)
  print('Generating Sheep')
  generate_obj_in_line(unit_manager, MAX_X, MAX_Y, 1, SHEEP_PER_PLAYER, SHEEP_RADIUS, PlayerId.GAIA, UnitInfo.SHEEP.ID)
  print('Generating Villagers')
  generate_villagers(unit_manager, MAX_X, MAX_Y)
  print('Finish!')

  scenario.write_to_file(output_path)

