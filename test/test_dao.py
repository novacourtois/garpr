import unittest
from dao import Dao, RegionNotFoundException, DuplicateAliasException, InvalidNameException
from bson.objectid import ObjectId
from model import *
from ming import mim
import trueskill
from datetime import datetime
import mongomock
from pymongo.errors import DuplicateKeyError

class TestDAO(unittest.TestCase):
    def setUp(self):
        self.region = 'test'
        self.mongo_client = mongomock.MongoClient()
        self.dao = Dao(self.region, mongo_client=self.mongo_client, new=True)

        self.player_1_id = ObjectId()
        self.player_2_id = ObjectId()
        self.player_3_id = ObjectId()
        self.player_4_id = ObjectId()
        self.player_5_id = ObjectId()
        self.player_1 = Player('gaR', ['gar', 'garr'], TrueskillRating(), False, id=self.player_1_id)
        self.player_2 = Player('sfat', ['sfat', 'miom | sfat'], TrueskillRating(), False, id=self.player_2_id)
        self.player_3 = Player('mango', ['mango'], 
                               TrueskillRating(trueskill_rating=trueskill.Rating(mu=2, sigma=3)), 
                               True, id=self.player_3_id)
        self.player_4 = Player('shroomed', ['shroomed'], TrueskillRating(), False, id=self.player_4_id)
        self.player_5 = Player('pewpewu', ['pewpewu'], TrueskillRating(), False, id=self.player_5_id)

        # only includes players 1-3
        self.players = [self.player_1, self.player_2, self.player_3]

        self.tournament_id_1 = ObjectId()
        self.tournament_type_1 = 'tio'
        self.tournament_raw_1 = 'raw1'
        self.tournament_date_1 = datetime(2013, 10, 16)
        self.tournament_name_1 = 'tournament 1'
        self.tournament_players_1 = [self.player_1_id, self.player_2_id, self.player_3_id, self.player_4_id]
        self.tournament_matches_1 = [
                MatchResult(winner=self.player_1_id, loser=self.player_2_id),
                MatchResult(winner=self.player_3_id, loser=self.player_4_id)
        ]

        # tournament 2 is earlier than tournament 1, but inserted after
        self.tournament_id_2 = ObjectId()
        self.tournament_type_2 = 'challonge'
        self.tournament_raw_2 = 'raw2'
        self.tournament_date_2 = datetime(2013, 10, 10)
        self.tournament_name_2 = 'tournament 2'
        self.tournament_players_2 = [self.player_5_id, self.player_2_id, self.player_3_id, self.player_4_id]
        self.tournament_matches_2 = [
                MatchResult(winner=self.player_5_id, loser=self.player_2_id),
                MatchResult(winner=self.player_3_id, loser=self.player_4_id)
        ]

        self.tournament_1 = Tournament(self.tournament_type_1,
                                       self.tournament_raw_1,
                                       self.tournament_date_1, 
                                       self.tournament_name_1,
                                       self.tournament_players_1,
                                       self.tournament_matches_1,
                                       id=self.tournament_id_1)

        self.tournament_2 = Tournament(self.tournament_type_2,
                                       self.tournament_raw_2,
                                       self.tournament_date_2, 
                                       self.tournament_name_2,
                                       self.tournament_players_2,
                                       self.tournament_matches_2,
                                       id=self.tournament_id_2)

        self.tournament_ids = [self.tournament_id_1, self.tournament_id_2]
        self.tournaments = [self.tournament_1, self.tournament_2]

        self.ranking_entry_1 = RankingEntry(1, self.player_1_id, 20)
        self.ranking_entry_2 = RankingEntry(2, self.player_2_id, 19)
        self.ranking_entry_3 = RankingEntry(3, self.player_3_id, 17.5)
        self.ranking_entry_4 = RankingEntry(3, self.player_4_id, 16.5)

        self.ranking_time_1 = datetime(2013, 4, 20)
        self.ranking_time_2 = datetime(2013, 4, 21)
        self.ranking_1 = Ranking(self.ranking_time_1, self.tournament_ids, 
                                 [self.ranking_entry_1, self.ranking_entry_2, self.ranking_entry_3])
        self.ranking_2 = Ranking(self.ranking_time_2, self.tournament_ids, 
                                 [self.ranking_entry_1, self.ranking_entry_2, self.ranking_entry_4])

        self.rankings = [self.ranking_1, self.ranking_2]

        for player in self.players:
            self.dao.add_player(player)

        for tournament in self.tournaments:
            self.dao.insert_tournament(tournament)

        for ranking in self.rankings:
            self.dao.insert_ranking(ranking)

    def test_init_with_invalid_region(self):
        print Dao.get_all_regions(mongo_client=self.mongo_client)
        # create a dao with an existing region
        Dao(self.region, mongo_client=self.mongo_client, new=False)

        # create a dao with a new region
        with self.assertRaises(RegionNotFoundException):
            Dao('newregion', mongo_client=self.mongo_client, new=False)

    def test_get_all_regions(self):
        # add another region
        region = 'newregion'
        Dao(region, mongo_client=self.mongo_client, new=True)

        self.assertEquals(set(Dao.get_all_regions(mongo_client=self.mongo_client)), set([self.region, region]))

    def test_get_player_by_id(self):
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id), self.player_1)
        self.assertEquals(self.dao.get_player_by_id(self.player_2_id), self.player_2)
        self.assertEquals(self.dao.get_player_by_id(self.player_3_id), self.player_3)
        self.assertIsNone(self.dao.get_player_by_id(ObjectId()))

    def test_get_player_by_alias(self):
        self.assertEquals(self.dao.get_player_by_alias('gar'), self.player_1)
        self.assertEquals(self.dao.get_player_by_alias('GAR'), self.player_1)
        self.assertEquals(self.dao.get_player_by_alias('garr'), self.player_1)
        self.assertEquals(self.dao.get_player_by_alias('sfat'), self.player_2)
        self.assertEquals(self.dao.get_player_by_alias('miom | sfat'), self.player_2)
        self.assertEquals(self.dao.get_player_by_alias('mango'), self.player_3)

        self.assertIsNone(self.dao.get_player_by_alias('miom|sfat'))
        self.assertIsNone(self.dao.get_player_by_alias(''))

    def test_get_all_players(self):
        self.assertEquals(self.dao.get_all_players(), [self.player_1, self.player_3, self.player_2])

    def test_add_player_duplicate(self):
        with self.assertRaises(DuplicateKeyError):
            self.dao.add_player(self.player_1)

    def test_delete_player(self):
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id), self.player_1)
        self.assertEquals(self.dao.get_player_by_id(self.player_2_id), self.player_2)
        self.assertEquals(self.dao.get_player_by_id(self.player_3_id), self.player_3)

        self.dao.delete_player(self.player_2)
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id), self.player_1)
        self.assertIsNone(self.dao.get_player_by_id(self.player_2_id))
        self.assertEquals(self.dao.get_player_by_id(self.player_3_id), self.player_3)

        self.dao.delete_player(self.player_3)
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id), self.player_1)
        self.assertIsNone(self.dao.get_player_by_id(self.player_2_id))
        self.assertIsNone(self.dao.get_player_by_id(self.player_3_id))

        self.dao.delete_player(self.player_1)
        self.assertIsNone(self.dao.get_player_by_id(self.player_1_id))
        self.assertIsNone(self.dao.get_player_by_id(self.player_2_id))
        self.assertIsNone(self.dao.get_player_by_id(self.player_3_id))

    def test_update_player(self):
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id), self.player_1)
        self.assertEquals(self.dao.get_player_by_id(self.player_2_id), self.player_2)
        self.assertEquals(self.dao.get_player_by_id(self.player_3_id), self.player_3)

        player_1_clone = Player('gar', ['gar', 'garr'], TrueskillRating(), False, id=self.player_1_id)
        player_1_clone.name = 'garrr'
        player_1_clone.aliases.append('garrr')
        player_1_clone.exclude = True
        self.assertNotEquals(self.dao.get_player_by_id(self.player_1_id), player_1_clone)

        self.dao.update_player(player_1_clone)

        self.assertNotEquals(self.dao.get_player_by_id(self.player_1_id), self.player_1)
        self.assertEquals(self.dao.get_player_by_id(self.player_2_id), self.player_2)
        self.assertEquals(self.dao.get_player_by_id(self.player_3_id), self.player_3)
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id), player_1_clone)

    def test_get_excluded_players(self):
        self.assertEquals(self.dao.get_excluded_players(), [self.player_3])

    def test_exclude_player(self):
        self.assertEquals(self.dao.get_excluded_players(), [self.player_3])

        self.assertFalse(self.player_1.exclude)
        self.dao.exclude_player(self.player_1)
        self.assertTrue(self.player_1.exclude)

        excluded_players = sorted(self.dao.get_excluded_players(), key=lambda p: p.name)
        self.assertEquals(len(excluded_players), 2)
        self.assertEquals(excluded_players[0], self.player_1)
        self.assertEquals(excluded_players[1], self.player_3)

    def test_include_player(self):
        self.assertEquals(self.dao.get_excluded_players(), [self.player_3])

        self.assertTrue(self.player_3.exclude)
        self.dao.include_player(self.player_3)
        self.assertFalse(self.player_3.exclude)

        self.assertEquals(self.dao.get_excluded_players(), [])

    def test_add_alias_to_player(self):
        new_alias = 'gaRRR'
        lowercase_alias = 'garrr'
        old_expected_aliases = ['gar', 'garr']
        new_expected_aliases = ['gar', 'garr', 'garrr']

        self.assertEquals(self.dao.get_player_by_id(self.player_1_id).aliases, old_expected_aliases)
        self.assertEquals(self.player_1.aliases, old_expected_aliases)
        self.dao.add_alias_to_player(self.player_1, new_alias)
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id).aliases, new_expected_aliases)
        self.assertEquals(self.player_1.aliases, new_expected_aliases)

    def test_add_alias_to_player_duplicate(self):
        with self.assertRaises(DuplicateAliasException):
            self.dao.add_alias_to_player(self.player_1, 'garr')

    def test_update_player_name(self):
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id).name, 'gaR')
        self.assertEquals(self.player_1.name, 'gaR')
        self.dao.update_player_name(self.player_1, 'gaRR')
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id).name, 'gaRR')
        self.assertEquals(self.player_1.name, 'gaRR')

    def test_update_player_name_non_alias(self):
        with self.assertRaises(InvalidNameException):
            self.dao.update_player_name(self.player_1, 'asdf')

    def test_reset_all_player_ratings(self):
        self.assertEquals(self.dao.get_player_by_id(self.player_1_id).rating, TrueskillRating())
        self.assertEquals(self.dao.get_player_by_id(self.player_2_id).rating, TrueskillRating())
        self.assertEquals(self.dao.get_player_by_id(self.player_3_id).rating, 
                          TrueskillRating(trueskill_rating=trueskill.Rating(mu=2, sigma=3)))

        self.dao.reset_all_player_ratings()

        self.assertEquals(self.dao.get_player_by_id(self.player_1_id).rating, TrueskillRating())
        self.assertEquals(self.dao.get_player_by_id(self.player_2_id).rating, TrueskillRating())
        self.assertEquals(self.dao.get_player_by_id(self.player_3_id).rating, TrueskillRating())

    def test_update_tournament(self):
        tournament_1 = self.dao.get_tournament_by_id(self.tournament_id_1)
        self.assertEquals(tournament_1.id, self.tournament_id_1)
        self.assertEquals(tournament_1.type, self.tournament_type_1)
        self.assertEquals(tournament_1.raw, self.tournament_raw_1)
        self.assertEquals(tournament_1.date, self.tournament_date_1)
        self.assertEquals(tournament_1.name, self.tournament_name_1)
        self.assertEquals(tournament_1.matches, self.tournament_matches_1)
        self.assertEquals(tournament_1.players, self.tournament_players_1)

        tournament_2 = self.dao.get_tournament_by_id(self.tournament_id_2)
        self.assertEquals(tournament_2.id, self.tournament_id_2)
        self.assertEquals(tournament_2.type, self.tournament_type_2)
        self.assertEquals(tournament_2.raw, self.tournament_raw_2)
        self.assertEquals(tournament_2.date, self.tournament_date_2)
        self.assertEquals(tournament_2.name, self.tournament_name_2)
        self.assertEquals(tournament_2.matches, self.tournament_matches_2)
        self.assertEquals(tournament_2.players, self.tournament_players_2)

        tournament_2_raw_new = 'asdfasdf'
        tournament_2_name_new = 'new tournament 2 name'

        tournament_2.raw = tournament_2_raw_new
        tournament_2.name = tournament_2_name_new

        self.dao.update_tournament(tournament_2)

        tournament_1 = self.dao.get_tournament_by_id(self.tournament_id_1)
        self.assertEquals(tournament_1.id, self.tournament_id_1)
        self.assertEquals(tournament_1.type, self.tournament_type_1)
        self.assertEquals(tournament_1.raw, self.tournament_raw_1)
        self.assertEquals(tournament_1.date, self.tournament_date_1)
        self.assertEquals(tournament_1.name, self.tournament_name_1)
        self.assertEquals(tournament_1.matches, self.tournament_matches_1)
        self.assertEquals(tournament_1.players, self.tournament_players_1)

        tournament_2 = self.dao.get_tournament_by_id(self.tournament_id_2)
        self.assertEquals(tournament_2.id, self.tournament_id_2)
        self.assertEquals(tournament_2.type, self.tournament_type_2)
        self.assertEquals(tournament_2.raw, tournament_2_raw_new)
        self.assertEquals(tournament_2.date, self.tournament_date_2)
        self.assertEquals(tournament_2.name, tournament_2_name_new)
        self.assertEquals(tournament_2.matches, self.tournament_matches_2)
        self.assertEquals(tournament_2.players, self.tournament_players_2)

    def test_get_all_tournaments(self):
        tournaments = self.dao.get_all_tournaments()

        self.assertEquals(len(tournaments), 2)

        # tournament 1 is last in the list because it occurs later than tournament 2
        tournament_1 = tournaments[1]
        self.assertEquals(tournament_1.id, self.tournament_id_1)
        self.assertEquals(tournament_1.type, self.tournament_type_1)
        self.assertEquals(tournament_1.raw, self.tournament_raw_1)
        self.assertEquals(tournament_1.date, self.tournament_date_1)
        self.assertEquals(tournament_1.name, self.tournament_name_1)
        self.assertEquals(tournament_1.matches, self.tournament_matches_1)
        self.assertEquals(tournament_1.players, self.tournament_players_1)

        tournament_2 = tournaments[0]
        self.assertEquals(tournament_2.id, self.tournament_id_2)
        self.assertEquals(tournament_2.type, self.tournament_type_2)
        self.assertEquals(tournament_2.raw, self.tournament_raw_2)
        self.assertEquals(tournament_2.date, self.tournament_date_2)
        self.assertEquals(tournament_2.name, self.tournament_name_2)
        self.assertEquals(tournament_2.matches, self.tournament_matches_2)
        self.assertEquals(tournament_2.players, self.tournament_players_2)
        
    def test_get_all_tournaments_containing_players(self):
        players = [self.player_5]

        tournaments = self.dao.get_all_tournaments(players=players)
        self.assertEquals(len(tournaments), 1)

        tournament = tournaments[0]
        self.assertEquals(tournament.id, self.tournament_id_2)
        self.assertEquals(tournament.type, self.tournament_type_2)
        self.assertEquals(tournament.raw, self.tournament_raw_2)
        self.assertEquals(tournament.date, self.tournament_date_2)
        self.assertEquals(tournament.name, self.tournament_name_2)
        self.assertEquals(tournament.matches, self.tournament_matches_2)
        self.assertEquals(tournament.players, self.tournament_players_2)

    def test_get_tournament_by_id(self):
        tournament_1 = self.dao.get_tournament_by_id(self.tournament_id_1)
        self.assertEquals(tournament_1.id, self.tournament_id_1)
        self.assertEquals(tournament_1.type, self.tournament_type_1)
        self.assertEquals(tournament_1.raw, self.tournament_raw_1)
        self.assertEquals(tournament_1.date, self.tournament_date_1)
        self.assertEquals(tournament_1.name, self.tournament_name_1)
        self.assertEquals(tournament_1.matches, self.tournament_matches_1)
        self.assertEquals(tournament_1.players, self.tournament_players_1)

        tournament_2 = self.dao.get_tournament_by_id(self.tournament_id_2)
        self.assertEquals(tournament_2.id, self.tournament_id_2)
        self.assertEquals(tournament_2.type, self.tournament_type_2)
        self.assertEquals(tournament_2.raw, self.tournament_raw_2)
        self.assertEquals(tournament_2.date, self.tournament_date_2)
        self.assertEquals(tournament_2.name, self.tournament_name_2)
        self.assertEquals(tournament_2.matches, self.tournament_matches_2)
        self.assertEquals(tournament_2.players, self.tournament_players_2)

        self.assertIsNone(self.dao.get_tournament_by_id(ObjectId()))

    def test_merge_players(self):
        self.dao.merge_players(source=self.player_5, target=self.player_1)

        tournament_1 = self.dao.get_tournament_by_id(self.tournament_id_1)
        self.assertEquals(tournament_1.id, self.tournament_id_1)
        self.assertEquals(tournament_1.type, self.tournament_type_1)
        self.assertEquals(tournament_1.raw, self.tournament_raw_1)
        self.assertEquals(tournament_1.date, self.tournament_date_1)
        self.assertEquals(tournament_1.name, self.tournament_name_1)
        self.assertEquals(tournament_1.matches, self.tournament_matches_1)
        self.assertEquals(tournament_1.players, self.tournament_players_1)

        tournament_2 = self.dao.get_tournament_by_id(self.tournament_id_2)
        self.assertEquals(tournament_2.id, self.tournament_id_2)
        self.assertEquals(tournament_2.type, self.tournament_type_2)
        self.assertEquals(tournament_2.raw, self.tournament_raw_2)
        self.assertEquals(tournament_2.date, self.tournament_date_2)
        self.assertEquals(tournament_2.name, self.tournament_name_2)
        self.assertEquals(set(tournament_2.players), set(self.tournament_players_1))
        self.assertEquals(len(tournament_2.matches), len(self.tournament_matches_1))
        self.assertEquals(tournament_2.matches[0], self.tournament_matches_1[0])
        self.assertEquals(tournament_2.matches[1], self.tournament_matches_1[1])

        merged_player_aliases = ['gar', 'garr', 'pewpewu']
        merged_player = self.dao.get_player_by_id(self.player_1_id)
        self.assertEquals(merged_player.id, self.player_1_id)
        self.assertEquals(merged_player.name, self.player_1.name)
        self.assertEquals(merged_player.aliases, merged_player_aliases)

        self.assertIsNone(self.dao.get_player_by_id(self.player_5_id))

    def test_merge_players_none(self):
        with self.assertRaises(TypeError):
            self.dao.merge_players()

        with self.assertRaises(TypeError):
            self.dao.merge_players(source=self.player_1)

        with self.assertRaises(TypeError):
            self.dao.merge_players(target=self.player_1)
    
    def test_merge_players_same_player(self):
        with self.assertRaises(ValueError):
            self.dao.merge_players(source=self.player_1, target=self.player_1)

    # TODO
    def test_merge_players_same_player_in_single_match(self):
        pass

    def test_get_latest_ranking(self):
        latest_ranking = self.dao.get_latest_ranking()

        self.assertEquals(latest_ranking.time, self.ranking_time_2)
        self.assertEquals(latest_ranking.tournaments, self.tournament_ids)

        rankings = latest_ranking.ranking
        
        self.assertEquals(len(rankings), 3)
        self.assertEquals(rankings[0], self.ranking_entry_1)
        self.assertEquals(rankings[1], self.ranking_entry_2)
        self.assertEquals(rankings[2], self.ranking_entry_4)
