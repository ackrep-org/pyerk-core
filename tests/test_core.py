import unittest
import sys
import os
from os.path import join as pjoin

import rdflib

# noinspection PyUnresolvedReferences
from ipydex import IPS, activate_ips_on_exception, set_trace
import pyerk as p
import pyerk.visualization as visualization

"""
recommended ways to run the tests from the repo root (where setup.py lives):

# all tests
nosetests --rednose --nocapture
python3 -m unititest

# single class


"""

activate_ips_on_exception()

current_dir = os.path.dirname(os.path.abspath(sys.modules.get(__name__).__file__))

ERK_ROOT_DIR = p.aux.get_erk_root_dir()

# path for basic (staged) test data
TEST_DATA_DIR1 = pjoin(ERK_ROOT_DIR, "pyerk", "tests", "test_data")

# path for "realistic" test data
TEST_DATA_PATH2 = pjoin(ERK_ROOT_DIR, "erk-data", "control-theory", "control_theory1.py")
TEST_MOD_NAME = "control_theory1"

__URI__ = TEST_BASE_URI = "local/unittest/"

# this serves to print the test-method-name before it is executed (useful for debugging, see setUP below)
PRINT_TEST_METHODNAMES = True

# some tests might generate files such as `tmp.svg` as a byproduct for debugging. The following flags controls this.
WRITE_TMP_FILES = False


class HouskeeperMixin:
    """
    Class to provide common functions for all our TestCase subclasses
    """
    def setUp(self):
        self.print_methodnames()
        self.register_this_module()

    def tearDown(self) -> None:
        self.unload_all_mods()

    @staticmethod
    def unload_all_mods():
        p.unload_mod(TEST_BASE_URI, strict=False)

        # unload all modules which where loaded by a test
        for mod_id in list(p.ds.mod_path_mapping.a.keys()):
            p.unload_mod(mod_id)

    @staticmethod
    def register_this_module():
        keymanager = p.KeyManager()
        p.register_mod(TEST_BASE_URI, keymanager)

    def print_methodnames(self):
        if PRINT_TEST_METHODNAMES:
            # noinspection PyUnresolvedReferences
            print("In method", p.aux.bgreen(self._testMethodName))


class TestCore0(HouskeeperMixin, unittest.TestCase):

    def test_a0__process_key_str(self):
        res = p.process_key_str("I1")
        self.assertEqual(res.prefix, None)
        self.assertEqual(res.short_key, "I1")
        self.assertEqual(res.label, None)

        res = p.process_key_str("I000__test_label", check=False)
        self.assertEqual(res.prefix, None)
        self.assertEqual(res.short_key, "I000")
        self.assertEqual(res.label, "test_label")

        res = p.process_key_str("some_prefix__I000", check=False, resolve_prefix=False)
        self.assertEqual(res.prefix, "some_prefix")
        self.assertEqual(res.short_key, "I000")
        self.assertEqual(res.label, None)

        res = p.process_key_str("some_prefix__I000__test_label", check=False, resolve_prefix=False)
        self.assertEqual(res.prefix, "some_prefix")
        self.assertEqual(res.short_key, "I000")
        self.assertEqual(res.label, "test_label")

        with self.assertRaises(p.UnknownPrefixError):
            res = p.process_key_str("some_prefix__I000__test_label", check=False, resolve_prefix=True)

        with self.assertRaises(KeyError):
            res = p.process_key_str("some_prefix_literal_value", check=False)

    def test_b1__uri_contex_manager(self):
        """
        Test defined behavior of errors occur in uri_context
        :return:
        """

        self.assertEqual(len(p.core._uri_stack), 0)
        try:
            with p.uri_context(uri=TEST_BASE_URI):
                raise ValueError
        except ValueError:
            pass
        self.assertEqual(len(p.core._uri_stack), 0)

        self.assertEqual(len(p.ds.entities_created_in_mod), 1)
        L1 = len(p.ds.items)
        L2 = len(p.ds.relations)
        L3 = len(p.ds.relation_edge_list)
        try:
            _ = p.erkloader.load_mod_from_path(pjoin(TEST_DATA_DIR1, "tmod0_with_errors.py"), prefix="tm0")
        except ValueError:
            pass
        # assert that no enties remain in the data structures
        self.assertEqual(len(p.ds.entities_created_in_mod), 1)
        self.assertEqual(L1, len(p.ds.items))
        self.assertEqual(L2, len(p.ds.relations))
        self.assertEqual(L3, len(p.ds.relation_edge_list))
        self.assertEqual(len(p.core._uri_stack), 0)

    def test_key_manager(self):
        p.KeyManager.instance = None

        km = p.KeyManager(minval=100, maxval=105)

        self.assertEqual(km.key_reservoir, [103, 101, 100, 104, 102])

        k = km.pop()
        self.assertEqual(k, 102)

        k = km.pop()
        self.assertEqual(k, 104)
        self.assertEqual(km.key_reservoir, [103, 101, 100])

    def test_uri_attr_of_entities(self):

        self.assertEqual(p.I1.uri, f"{p.BUILTINS_URI}#I1")
        self.assertEqual(p.R1.uri, f"{p.BUILTINS_URI}#R1")

        with self.assertRaises(p.EmptyURIStackError) as cm:
            itm = p.create_item(key_str=p.pop_uri_based_key("I"), R1="unit test item")

        with p.uri_context(uri=TEST_BASE_URI):
            itm = p.create_item(key_str=p.pop_uri_based_key("I"), R1="unit test item")
            rel = p.create_relation(key_str=p.pop_uri_based_key("R"), R1="unit test relation")

        self.assertEqual(itm.uri, f"{TEST_BASE_URI}#{itm.short_key}")
        self.assertEqual(rel.uri, f"{TEST_BASE_URI}#{rel.short_key}")

    def test_load_multiple_modules(self):
        tmod1 = p.erkloader.load_mod_from_path(pjoin(TEST_DATA_DIR1, "tmod1.py"), prefix="tm1")
        # TODO: to be continued where tmod1 itself loads tmod2...


# noinspection PyPep8Naming
class TestCore1(HouskeeperMixin, unittest.TestCase):

    def test_aa0__directory_structure(self):
        pyerk_dir = pjoin(ERK_ROOT_DIR, "pyerk")
        django_gui_dir = pjoin(ERK_ROOT_DIR, "django-erk-gui")
        erk_data_dir = pjoin(ERK_ROOT_DIR, "erk-data")

        self.assertTrue(os.path.isdir(pyerk_dir))
        self.assertTrue(os.path.isdir(django_gui_dir))
        self.assertTrue(os.path.isdir(erk_data_dir))

    def test_aa1(self):
        """
        The first test ensures, that TestCases do not influence each other
        """

        mod1 = p.erkloader.load_mod_from_path(TEST_DATA_PATH2, prefix="ct")

        self.tearDown()

        # after tearing down there should be no i32 instances left
        i32_instance_rels = p.I32["evaluated mapping"].get_inv_relations("R4__is_instance_of")
        self.assertEqual(len(i32_instance_rels), 0)

        builtin_entity_uris = set(p.ds.entities_created_in_mod[p.BUILTINS_URI])
        builtin_rledg_uris = set(p.ds.rledgs_created_in_mod[p.BUILTINS_URI])
        available_item_keys = set(p.ds.items.keys())
        available_relation_keys = set(p.ds.relations.keys())
        available_relation_edge_keys = set(p.ds.relation_edge_uri_map.keys())
        available_relation_relation_edge_keys = set(p.ds.relation_relation_edges.keys())

        diff1 = available_item_keys.difference(builtin_entity_uris)
        diff2 = available_relation_keys.difference(builtin_entity_uris)

        diff3 = available_relation_edge_keys.difference(builtin_rledg_uris)
        diff4 = available_relation_relation_edge_keys.difference(builtin_entity_uris)

        self.assertEqual(len(diff1), 0)
        self.assertEqual(len(diff2), 0)
        self.assertEqual(len(diff3), 0)
        self.assertEqual(len(diff4), 0)

    # noinspection PyUnresolvedReferences
    # (above noinspection is necessary because of the @-operator which is undecleared for strings)
    def test_core1(self):
        mod1 = p.erkloader.load_mod_from_path(TEST_DATA_PATH2, prefix="ct")
        self.assertEqual(mod1.I3749.R1, "Cayley-Hamilton theorem")

        def_eq_item = mod1.I6886.R6__has_defining_equation
        self.assertEqual(def_eq_item.R4__is_instance_of, p.I18["mathematical expression"])
        self.assertEqual(def_eq_item.R24__has_LaTeX_string, r"$\dot x = f(x, u)$")

        teststring1 = "this is english text" @ p.en
        teststring2 = "das ist deutsch" @ p.de

        self.assertIsInstance(teststring1, rdflib.Literal)
        self.assertIsInstance(teststring2, rdflib.Literal)

        # R1 should return the default
        self.assertEqual(p.I900.R1.language, p.settings.DEFAULT_DATA_LANGUAGE)

        # ensure that R32["is functional for each language"] works as expected (return str/Literal but not [str] ...)
        self.assertNotIsInstance(p.I12.R2, list)
        self.assertNotIsInstance(p.I900.R2, list)

        p.unload_mod('pyerk/ocse/0.2')

    def test_b01_builtins1(self):
        """
        Test the mechanism to endow the Entity class with custom methods (on class and on instance level)
        :return:
        """
        # class level
        def example_func(slf, a):
            return f"{slf.R1}--{a}"

        p.Entity.add_method_to_class(example_func)

        res = p.I12.example_func("test")
        self.assertEqual("mathematical object--test", res)

        # instance level
        # Note: this creates items with keys which might conflict with recently added keys to builtin entities
        # explicitly unlinking them at the end

        with p.uri_context(uri=TEST_BASE_URI):
            itm = p.create_item(key_str=p.pop_uri_based_key("I"), R1="unit test item")
            itm2 = p.create_item(key_str=p.pop_uri_based_key("I"), R1="unit test item2")

        def example_func2(slf, a):
            return f"{slf.R1}::{a}"

        itm.add_method(example_func2)

        res2 = itm.example_func2(1234)
        self.assertEqual("unit test item::1234", res2)
        self.assertIsInstance(itm2, p.Entity)

        # ensure that this method is not available to generic other instances of Entity
        with self.assertRaises(AttributeError):
            itm2.example_func2(1234)

    def test_b02_tear_down(self):
        """
        test if tear_down of TestClass works properly

        :return:
        """

        # ensure that builtins are loaded
        self.assertGreater(len(p.ds.items), 40)
        self.assertGreater(len(p.ds.relations), 40)
        self.assertGreater(len(p.ds.relation_edge_uri_map), 300)

        # ensure that no residuals are left from last test
        non_builtin_rledges = [k for k in p.ds.relation_edge_uri_map.keys() if not k.startswith(p.BUILTINS_URI)]
        self.assertEqual(len(non_builtin_rledges), 0)

        non_builtin_entities = [k for k in p.ds.items.keys() if not k.startswith(p.BUILTINS_URI)]
        non_builtin_entities += [k for k in p.ds.relations.keys() if not k.startswith(p.BUILTINS_URI)]
        self.assertEqual(len(non_builtin_entities), 0)

    def test_evaluated_mapping(self):

        res = p.ds.relation_edges.get("RE6229")
        self.assertIsNone(res)

        mod1 = p.erkloader.load_mod_from_path(TEST_DATA_PATH2, prefix="ct")
        with p.uri_context(uri=TEST_BASE_URI):
            poly1 = p.instance_of(mod1.I4239["monovariate polynomial"])

        # test that an arbitrary item is *not* callable
        self.assertRaises(TypeError, mod1.I2738["field of complex numnbers"], 0)

        # test that some special items are callable (note that its parent class is a subclass of one which has
        # a _custom_call-method defined)
        with p.uri_context(uri=TEST_BASE_URI):
            # this creates new items and thus must be executed inside a context
            res = poly1(0)

        self.assertEqual(res.R4__is_instance_of, p.I32["evaluated mapping"])

    def test_evaluated_mapping2(self):
        mod1 = p.erkloader.load_mod_from_path(TEST_DATA_PATH2, prefix="ct")

        with p.uri_context(uri=TEST_BASE_URI):
            h = p.instance_of(mod1.I9923["scalar field"])
            f = p.instance_of(mod1.I9841["vector field"])
            x = p.instance_of(mod1.I1168["point in state space"])

            Lderiv = mod1.I1347["Lie derivative of scalar field"]
            h2 = Lderiv(h, f, x)

        self.assertEqual(h2.R4__is_instance_of, p.I32["evaluated mapping"])

        arg_tup = h2.R36__has_argument_tuple
        self.assertEqual(arg_tup.R4__is_instance_of, p.I33["tuple"])
        elements = arg_tup.R39__has_element
        self.assertEqual(tuple(elements), (h, f, x))

    def test_tuple(self):

        data = (10, 11, 12, 13, p.I1, "some string")
        tup = p.new_tuple(*data)
        self.assertEqual(tup.R4__is_instance_of, p.I33["tuple"])
        self.assertEqual(tup.R38__has_length, 6)

        # TODO: non functional relations should return a tuple not a list?
        res = tup.R39__has_element
        self.assertEqual(data, tuple(res))

    def test_scope_vars(self):

        # this tests for a bug with labels of scope vars
        mod1 = p.erkloader.load_mod_from_path(TEST_DATA_PATH2, prefix="ct")
        def_itm = p.ds.get_entity_by_key_str("I9907")
        matrix_instance = def_itm.M
        self.assertEqual(matrix_instance.R1, "M")

    def test_relations_with_sequence_as_argument(self):
        Ia001 = p.create_item(R1__has_label="test item")

        # check that assigning sequences is not allowed
        with self.assertRaises(TypeError):
            Ia001.set_relation(p.R5["is part of"], [p.I4["Mathematics"], p.I5["Engineering"]])

        mod1 = p.erkloader.load_mod_from_path(TEST_DATA_PATH2, prefix="ct")
        itm = p.ds.get_entity_by_key_str("I4466")  # I4466["Systems Theory"]
        # construction: R5__is_part_of=[p.I4["Mathematics"], p.I5["Engineering"]]
        res = itm.R5
        self.assertEqual(len(res), 2)
        self.assertIn(p.I4["Mathematics"], res)
        self.assertIn(p.I5["Engineering"], res)

    def test_is_instance_of_generalized_metaclass(self):
        mod1 = p.erkloader.load_mod_from_path(TEST_DATA_PATH2, prefix="ct")

        itm1 = p.ds.get_entity_by_key_str("I2__Metaclass")
        itm2 = p.ds.get_entity_by_key_str("ct__I4235__mathematical_object")
        itm3 = p.ds.get_entity_by_key_str("ct__I4239__monovariate_polynomial")

        # metaclass itself is not an instance of metaclass
        self.assertFalse(p.is_instance_of_generalized_metaclass(itm1))

        self.assertTrue(p.is_instance_of_generalized_metaclass(itm2))
        self.assertTrue(p.is_instance_of_generalized_metaclass(itm3))

        with p.uri_context(uri=TEST_BASE_URI):
            itm4 = p.instance_of(itm3)
        self.assertFalse(p.is_instance_of_generalized_metaclass(itm4))

    def test_qualifiers(self):
        mod1 = p.erkloader.load_mod_from_path(TEST_DATA_PATH2, prefix="ct")

        itm1: p.Item = p.ds.get_entity_by_key_str("I2746__Rudolf_Kalman")
        rel1, rel2 = itm1.get_relations()[p.pk("R1833__has_employer")][:2]
        self.assertEqual(len(rel1.qualifiers), 2)
        self.assertEqual(len(rel2.qualifiers), 2)

    def test_equation(self):
        mod1 = p.erkloader.load_mod_from_path(TEST_DATA_PATH2, prefix="ct")

        # get item via prefix and key
        itm1: p.Item = p.ds.get_entity_by_key_str("ct__I3749__Cayley-Hamilton_theorem")

        # get item via key and uri
        itm2: p.Item = p.ds.get_entity_by_key_str("I3749__Cayley-Hamilton_theorem", mod_uri=mod1.__URI__)

        self.assertEqual(itm1, itm2)

        Z: p.Item = itm1.scope("context").namespace["Z"]

        r31_list = Z.get_inv_relations("R31__is_in_mathematical_relation_with")
        re: p.RelationEdge = r31_list[0]
        self.assertEqual(len(r31_list), 1)

        # test the expected qualifier
        q = re.qualifiers[0]
        self.assertEqual(q.relation_tuple[0], re)
        self.assertEqual(q.relation_tuple[1], p.R34["has proxy item"])

        # this is the proxy item
        eq = q.relation_tuple[2]
        rhs = eq.R27__has_rhs
        self.assertEqual(rhs, Z)

        # ensure reproducible results of applied mappings
        lhs = eq.R26__has_lhs
        P: p.Item = itm1.scope("context").namespace["P"]
        A: p.Item = itm1.scope("context").namespace["A"]
        tmp = P(A)
        self.assertEqual(lhs, tmp)

    def test_process_key_str(self):

        # first, check label consistency in builtin_enities
        # note these keys do not to exist
        pkey1 = p.process_key_str("I0008234")

        self.assertEqual(pkey1.short_key, "I0008234")
        self.assertEqual(pkey1.label, None)

        pkey2 = p.process_key_str("R00001234__my_label")

        self.assertEqual(pkey2.short_key, "R00001234")
        self.assertEqual(pkey2.label, "my_label")

        # wrong syntax of key_str (missing "__")
        self.assertRaises(p.InvalidShortKeyError, p.process_key_str, "R1234XYZ")

        pkey3 = p.process_key_str("R2__has_description")

        self.assertEqual(pkey3.short_key, "R2")
        self.assertEqual(pkey3.label, "has_description")

        # wrong label ("_XYZ")
        self.assertRaises(ValueError, p.process_key_str, "R2__has_description_XYZ")

        # now, check label consistency in the test data
        mod1 = p.erkloader.load_mod_from_path(TEST_DATA_PATH2, TEST_MOD_NAME)

    def test_format_label(self):
        with p.uri_context(uri=TEST_BASE_URI):
            e1 = p.create_item(key_str="I0123", R1="1234567890")
        node = visualization.create_node(e1, url_template="")
        node.perform_html_wrapping(use_html=False)
        label = node.get_dot_label(render=True)
        self.assertEqual(label, 'I0123\\n["1234567890"]')

        with p.uri_context(uri=TEST_BASE_URI):
            e1 = p.create_item(key_str="I0124", R1="1234567890abcdefgh")
        node = visualization.create_node(e1, url_template="")
        node.perform_html_wrapping(use_html=False)
        label = node.get_dot_label(render=True)
        self.assertEqual(label, 'I0124\\n["1234567890abcde\\nfgh"]')

        with p.uri_context(uri=TEST_BASE_URI):
            e1 = p.create_item(key_str="I0125", R1="12 34567 890abcdefgh")
        node = visualization.create_node(e1, url_template="")
        node.perform_html_wrapping(use_html=False)
        label = node.get_dot_label(render=True)
        self.assertEqual(label, 'I0125\\n["12 34567\\n890abcdefgh"]')

        with p.uri_context(uri=TEST_BASE_URI):
            e1 = p.create_item(key_str="I0126", R1="12 34567-890abcdefgh")
        node = visualization.create_node(e1, url_template="")
        node.perform_html_wrapping(use_html=False)
        label = node.get_dot_label(render=True)
        self.assertEqual(label, 'I0126\\n["12 34567-\\n890abcdefgh"]')

    def test_visualization(self):

        res_graph: visualization.nx.DiGraph = visualization.create_nx_graph_from_entity("I21__mathematical_relation")
        self.assertEqual(res_graph.number_of_nodes(), 7)

        mod1 = p.erkloader.load_mod_from_path(TEST_DATA_PATH2, TEST_MOD_NAME)

        # do not use something like "Ia3699" here directly because this might change when mod1 changes
        auto_item: p.Item = mod1.I3749["Cayley-Hamilton theorem"].A
        res_graph: visualization.nx.DiGraph = visualization.create_nx_graph_from_entity(auto_item.short_key)
        self.assertEqual(res_graph.number_of_nodes(), 8)

    def test_visualization2(self):
        # test rendering of dot

        res = visualization.visualize_entity("I21__mathematical_relation", write_tmp_files=WRITE_TMP_FILES)

        mod1 = p.erkloader.load_mod_from_path(TEST_DATA_PATH2, TEST_MOD_NAME)
        auto_item: p.Item = mod1.I3749["Cayley-Hamilton theorem"].P
        res = visualization.visualize_entity(auto_item.short_key, write_tmp_files=WRITE_TMP_FILES)

        s1 = '<a href="">R35</a>'
        s2 = '<a href="">["is applied</a>'
        s3 = '<a href="">mapping of"]</a>'
        self.assertIn(s1, res)
        self.assertIn(s2, res)
        self.assertIn(s3, res)


class TestCore2(HouskeeperMixin, unittest.TestCase):

    def test_ruleengine1(self):
        # test rendering of dot
        p.ruleengine.apply_all_semantic_rules()


class TestZZCore3(HouskeeperMixin, unittest.TestCase):
    """
    Collection of test that should be executed last (because they seem to influence othter tests).
    This is achieved by putting "ZZ" in the name (assuming that test classes are executed in alphabetical order).
    """

    def test_sparql_query(self):
        # This test seems somehow to influence later tests
        mod1 = p.erkloader.load_mod_from_path(TEST_DATA_PATH2, TEST_MOD_NAME)
        p.ds.rdfgraph = p.rdfstack.create_rdf_triples()
        qsrc = p.rdfstack.get_sparql_example_query()
        res = p.ds.rdfgraph.query(qsrc)
        res2 = p.aux.apply_func_to_table_cells(p.rdfstack.convert_from_rdf_to_pyerk, res)

        # Note this will fail if more `R5__has_part` relations are used
        expected_result = [
            [mod1.I4466["Systems Theory"], p.I4["Mathematics"]],
            [mod1.I4466["Systems Theory"], p.I5["Engineering"]],
        ]
        self.assertEqual(res2, expected_result)

    def test_sparql_query2(self):
        # TODO: replace by Model entity once it exists
        mod1 = p.erkloader.load_mod_from_path(TEST_DATA_PATH2, TEST_MOD_NAME)

        m1 = p.instance_of(mod1.I7641["general system model"], r1="test_model 1", r2="a test model")
        m2 = p.instance_of(mod1.I7641["general system model"], r1="test_model 2", r2="a test model")

        m1.set_relation(p.R16["has property"], mod1.I9210["stabilizability"])
        m2.set_relation(p.R16["has property"], mod1.I7864["controllability"])

        # graph has to be created after the entities
        p.ds.rdfgraph = p.rdfstack.create_rdf_triples()

        qsrc = f"""
        PREFIX : <{p.rdfstack.ERK_URI}>
        SELECT ?s ?o
        WHERE {{
            ?s :R16 :I7864.
        }}
        """
        res = p.ds.rdfgraph.query(qsrc)
        res2 = p.aux.apply_func_to_table_cells(p.rdfstack.convert_from_rdf_to_pyerk, res)

        expected_result = [
            [m2["test_model 2"], None],
        ]
        self.assertEqual(res2, expected_result)
