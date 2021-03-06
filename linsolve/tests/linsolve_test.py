from __future__ import absolute_import, division, print_function
import unittest
import linsolve
import numpy as np
import ast

class TestLinSolve(unittest.TestCase):
    def test_ast_getterms(self):
        n = ast.parse('x+y',mode='eval')
        terms = linsolve.ast_getterms(n)
        self.assertEqual(terms, [['x'],['y']])
        n = ast.parse('x-y',mode='eval')
        terms = linsolve.ast_getterms(n)
        self.assertEqual(terms, [['x'],[-1,'y']])
        n = ast.parse('3*x-y',mode='eval')
        terms = linsolve.ast_getterms(n)
        self.assertEqual(terms, [[3,'x'],[-1,'y']])
    def test_unary(self):
        n = ast.parse('-x+y',mode='eval')
        terms = linsolve.ast_getterms(n)
        self.assertEqual(terms, [[-1,'x'],['y']])
    def test_multiproducts(self):
        n = ast.parse('a*x+a*b*c*y',mode='eval')
        terms = linsolve.ast_getterms(n)
        self.assertEqual(terms, [['a','x'],['a','b','c','y']])
        n = ast.parse('-a*x+a*b*c*y',mode='eval')
        terms = linsolve.ast_getterms(n)
        self.assertEqual(terms, [[-1,'a','x'],['a','b','c','y']])
        n = ast.parse('a*x-a*b*c*y',mode='eval')
        terms = linsolve.ast_getterms(n)
        self.assertEqual(terms, [['a','x'],[-1,'a','b','c','y']])
    def test_taylorexpand(self):
        terms = linsolve.taylor_expand([['x','y','z']],prepend='d')
        self.assertEqual(terms, [['x','y','z'],['dx','y','z'],['x','dy','z'],['x','y','dz']])
        terms = linsolve.taylor_expand([[1,'y','z']],prepend='d')
        self.assertEqual(terms, [[1,'y','z'],[1,'dy','z'],[1,'y','dz']])
        terms = linsolve.taylor_expand([[1,'y','z']],consts={'y':3}, prepend='d')
        self.assertEqual(terms, [[1,'y','z'],[1,'y','dz']])
    def test_verify_weights(self):
        self.assertEqual(linsolve.verify_weights({},['a']), {'a':1})
        self.assertEqual(linsolve.verify_weights(None,['a']), {'a':1})
        self.assertEqual(linsolve.verify_weights({'a':10.0},['a']), {'a': 10.0})
        self.assertRaises(AssertionError, linsolve.verify_weights, {'a':1.0+1.0j}, ['a'])
        self.assertRaises(AssertionError, linsolve.verify_weights, {'a':1.0}, ['a', 'b'])
    def test_infer_dtype(self):
        self.assertEqual(linsolve.infer_dtype([1.,2.]), np.float32)
        self.assertEqual(linsolve.infer_dtype([3,4]), np.float32)
        self.assertEqual(linsolve.infer_dtype([np.float32(1),4]), np.float32)
        self.assertEqual(linsolve.infer_dtype([np.float64(1),4]), np.float64)
        self.assertEqual(linsolve.infer_dtype([np.float32(1),4j]), np.complex64)
        self.assertEqual(linsolve.infer_dtype([np.float64(1),4j]), np.complex128)
        self.assertEqual(linsolve.infer_dtype([np.complex64(1),4j]), np.complex64)
        self.assertEqual(linsolve.infer_dtype([np.complex64(1),4.]), np.complex64)
        self.assertEqual(linsolve.infer_dtype([np.complex128(1),np.float64(4.)]), np.complex128)
        self.assertEqual(linsolve.infer_dtype([np.complex64(1),np.float64(4.)]), np.complex128)
        self.assertEqual(linsolve.infer_dtype([np.complex64(1),np.int32(4.)]), np.complex128)
        self.assertEqual(linsolve.infer_dtype([np.complex64(1),np.int64(4.)]), np.complex128)
    
class TestLinearEquation(unittest.TestCase):
    def test_basics(self):
        le = linsolve.LinearEquation('x+y')
        self.assertEqual(le.terms, [['x'],['y']])
        self.assertEqual(le.consts, {})
        self.assertEqual(len(le.prms), 2)
        le = linsolve.LinearEquation('x-y')
        self.assertEqual(le.terms, [['x'],[-1,'y']])
        le = linsolve.LinearEquation('a*x+b*y',a=1,b=2)
        self.assertEqual(le.terms, [['a','x'],['b','y']])
        self.assertTrue('a' in le.consts)
        self.assertTrue('b' in le.consts)
        self.assertEqual(len(le.prms), 2)
        le = linsolve.LinearEquation('a*x-b*y',a=1,b=2)
        self.assertEqual(le.terms, [['a','x'],[-1,'b','y']])
    def test_more(self):
        consts = {'g5':1,'g1':1}
        for k in ['g5*bl95', 'g1*bl111', 'g1*bl103']:
            le = linsolve.LinearEquation(k,**consts)
        self.assertEqual(le.terms[0][0][0], 'g')
    def test_unary(self):
        le = linsolve.LinearEquation('-a*x-b*y',a=1,b=2)
        self.assertEqual(le.terms, [[-1,'a','x'],[-1,'b','y']])
    def test_order_terms(self):
        le = linsolve.LinearEquation('x+y')
        terms = [[1,1,'x'],[1,1,'y']]
        self.assertEqual(terms, le.order_terms([[1,1,'x'],[1,1,'y']]))
        terms2 = [[1,1,'x'],[1,'y',1]]
        self.assertEqual(terms, le.order_terms([[1,1,'x'],[1,'y',1]]))
        le = linsolve.LinearEquation('a*x-b*y',a=2,b=4)
        terms = [[1,'a','x'],[1,'b','y']]
        self.assertEqual(terms, le.order_terms([[1,'a','x'],[1,'b','y']]))
        terms2 = [[1,'x','a'],[1,'b','y']]
        self.assertEqual(terms, le.order_terms([[1,'x','a'],[1,'b','y']]))
        le = linsolve.LinearEquation('g5*bl95+g1*bl111',g5=1,g1=1)
        terms = [['g5','bl95'],['g1','bl111']]
        self.assertEqual(terms, le.order_terms([['g5','bl95'],['g1','bl111']]))
    def test_term_check(self):
        le = linsolve.LinearEquation('a*x-b*y',a=2,b=4)
        terms = [[1,'a','x'],[1,'b','y']]
        self.assertEqual(terms, le.order_terms([[1,'a','x'],[1,'b','y']]))
        terms4 = [['c','x','a'],[1,'b','y']]
        self.assertRaises(AssertionError, le.order_terms, terms4)
        terms5 = [[1,'a','b'],[1,'b','y']]
        self.assertRaises(AssertionError, le.order_terms, terms5)
    def test_eval(self):
        le = linsolve.LinearEquation('a*x-b*y',a=2,b=4)
        sol = {'x':3, 'y':7}
        self.assertEqual(2*3-4*7, le.eval(sol))
        sol = {'x':3*np.ones(4), 'y':7*np.ones(4)}
        np.testing.assert_equal(2*3-4*7, le.eval(sol))
        le = linsolve.LinearEquation('x_-y')
        sol = {'x':3+3j*np.ones(10), 'y':7+2j*np.ones(10)}
        ans = np.conj(sol['x']) - sol['y']
        np.testing.assert_equal(ans, le.eval(sol))
        

class TestLinearSolver(unittest.TestCase):
    def setUp(self):
        self.sparse = False
        eqs = ['x+y','x-y']
        x,y = 1,2
        d,w = {}, {}
        for eq in eqs: d[eq],w[eq] = eval(eq), 1.
        self.ls = linsolve.LinearSolver(d,w,sparse=self.sparse)
    def test_basics(self):
        self.assertEqual(len(self.ls.prms),2)
        self.assertEqual(len(self.ls.eqs), 2)
        self.assertEqual(self.ls.eqs[0].terms, [['x'],['y']])
        self.assertEqual(self.ls.eqs[1].terms, [['x'],[-1,'y']])
    def test_get_A(self):
        self.ls.prm_order = {'x':0,'y':1} # override random default ordering
        A = self.ls.get_A()
        self.assertEqual(A.shape, (2,2,1))
        #np.testing.assert_equal(A.todense(), np.array([[1.,1],[1.,-1]]))
        np.testing.assert_equal(A, np.array([[[1.], [1]],[[1.],[-1]]]))
    #def test_get_AtAiAt(self):
    #    self.ls.prm_order = {'x':0,'y':1} # override random default ordering
    #    AtAiAt = self.ls.get_AtAiAt().squeeze()
    #    #np.testing.assert_equal(AtAiAt.todense(), np.array([[.5,.5],[.5,-.5]]))
    #    #np.testing.assert_equal(AtAiAt, np.array([[.5,.5],[.5,-.5]]))
    #    measured = np.array([[3.],[-1]])
    #    x,y = AtAiAt.dot(measured).flatten()
    #    self.assertAlmostEqual(x, 1.)
    #    self.assertAlmostEqual(y, 2.)
    def test_solve(self):
        sol = self.ls.solve()
        self.assertAlmostEqual(sol['x'], 1.)
        self.assertAlmostEqual(sol['y'], 2.)
    def test_solve_modes(self):
        for mode in ['default','lsqr','pinv','solve']:
            sol = self.ls.solve(mode=mode)
            self.assertAlmostEqual(sol['x'], 1.)
            self.assertAlmostEqual(sol['y'], 2.)
    def test_solve_arrays(self):
        x = np.arange(100,dtype=np.float); x.shape = (10,10)
        y = np.arange(100,dtype=np.float); y.shape = (10,10)
        eqs = ['2*x+y','-x+3*y']
        d,w = {}, {}
        for eq in eqs: d[eq],w[eq] = eval(eq), 1.
        ls = linsolve.LinearSolver(d,w, sparse=self.sparse)
        sol = ls.solve()
        np.testing.assert_almost_equal(sol['x'], x)
        np.testing.assert_almost_equal(sol['y'], y)
    def test_solve_arrays_modes(self):
        x = np.arange(100,dtype=np.float); x.shape = (10,10)
        y = np.arange(100,dtype=np.float); y.shape = (10,10)
        eqs = ['2*x+y','-x+3*y']
        d,w = {}, {}
        for eq in eqs: d[eq],w[eq] = eval(eq), 1.
        ls = linsolve.LinearSolver(d,w, sparse=self.sparse)
        for mode in ['default','lsqr','pinv','solve']:
            sol = ls.solve(mode=mode)
            np.testing.assert_almost_equal(sol['x'], x)
            np.testing.assert_almost_equal(sol['y'], y)
    def test_A_shape(self):
        consts = {'a':np.arange(10), 'b':np.zeros((1,10))}
        ls = linsolve.LinearSolver({'a*x+b*y':0.},{'a*x+b*y':1},**consts)
        self.assertEqual(ls._A_shape(), (1,2,10*10))
    def test_const_arrays(self):
        x,y = 1.,2.
        a = np.array([3.,4,5])
        b = np.array([1.,2,3])
        eqs = ['a*x+y','x+b*y']
        d,w = {}, {}
        for eq in eqs: d[eq],w[eq] = eval(eq), 1.
        ls = linsolve.LinearSolver(d,w,a=a,b=b, sparse=self.sparse)
        sol = ls.solve()
        np.testing.assert_almost_equal(sol['x'], x*np.ones(3,dtype=np.float))
        np.testing.assert_almost_equal(sol['y'], y*np.ones(3,dtype=np.float))
    def test_wgt_arrays(self):
        x,y = 1.,2.
        a,b = 3.,1.
        eqs = ['a*x+y','x+b*y']
        d,w = {}, {}
        for eq in eqs: d[eq],w[eq] = eval(eq), np.ones(4)
        ls = linsolve.LinearSolver(d,w,a=a,b=b, sparse=self.sparse)
        sol = ls.solve()
        np.testing.assert_almost_equal(sol['x'], x*np.ones(4,dtype=np.float))
        np.testing.assert_almost_equal(sol['y'], y*np.ones(4,dtype=np.float))
    def test_wgt_const_arrays(self):
        x,y = 1.,2.
        a,b = 3.*np.ones(4),1.
        eqs = ['a*x+y','x+b*y']
        d,w = {}, {}
        for eq in eqs: d[eq],w[eq] = eval(eq)*np.ones(4), np.ones(4)
        ls = linsolve.LinearSolver(d,w,a=a,b=b, sparse=self.sparse)
        sol = ls.solve()
        np.testing.assert_almost_equal(sol['x'], x*np.ones(4,dtype=np.float))
        np.testing.assert_almost_equal(sol['y'], y*np.ones(4,dtype=np.float))
    def test_nonunity_wgts(self):
        x,y = 1.,2.
        a,b = 3.*np.ones(4),1.
        eqs = ['a*x+y','x+b*y']
        d,w = {}, {}
        for eq in eqs: d[eq],w[eq] = eval(eq)*np.ones(4), 2*np.ones(4)
        ls = linsolve.LinearSolver(d,w,a=a,b=b, sparse=self.sparse)
        sol = ls.solve()
        np.testing.assert_almost_equal(sol['x'], x*np.ones(4,dtype=np.float))
        np.testing.assert_almost_equal(sol['y'], y*np.ones(4,dtype=np.float))
    def test_eval(self):
        x,y = 1.,2.
        a,b = 3.*np.ones(4),1.
        eqs = ['a*x+y','x+b*y']
        d,w = {}, {}
        for eq in eqs: d[eq],w[eq] = eval(eq)*np.ones(4), np.ones(4)
        ls = linsolve.LinearSolver(d,w,a=a,b=b, sparse=self.sparse)
        sol = ls.solve()
        np.testing.assert_almost_equal(sol['x'], x*np.ones(4,dtype=np.float))
        np.testing.assert_almost_equal(sol['y'], y*np.ones(4,dtype=np.float))
        result = ls.eval(sol)
        for eq in d:
            np.testing.assert_almost_equal(d[eq], result[eq])
        result = ls.eval(sol, 'a*x+b*y')
        np.testing.assert_almost_equal(3*1+1*2, list(result.values())[0])
    def test_chisq(self):
        x = 1.
        d = {'x':1, 'a*x':2}
        ls = linsolve.LinearSolver(d,a=1.0, sparse=self.sparse)
        sol = ls.solve()
        chisq = ls.chisq(sol)
        np.testing.assert_equal(chisq, .5)
        x = 1.
        d = {'x':1, '1.0*x':2}
        ls = linsolve.LinearSolver(d, sparse=self.sparse)
        sol = ls.solve()
        chisq = ls.chisq(sol)
        np.testing.assert_equal(chisq, .5)
        x = 1.
        d = {'1*x': 2.0, 'x': 1.0}
        w = {'1*x': 1.0, 'x': .5}
        ls = linsolve.LinearSolver(d, wgts=w, sparse=self.sparse)
        sol = ls.solve()
        chisq = ls.chisq(sol)
        self.assertAlmostEqual(sol['x'], 5.0/3.0)
        self.assertAlmostEqual(ls.chisq(sol), 1.0/3.0)
    def test_dtypes(self):
        ls = linsolve.LinearSolver({'x_': 1.0+1.0j}, sparse=self.sparse)
        self.assertEqual(ls.dtype,np.float32)
        self.assertEqual(type(ls.solve()['x']), np.complex64)

        ls = linsolve.LinearSolver({'x': 1.0+1.0j}, sparse=self.sparse)
        self.assertEqual(ls.dtype, np.complex64)
        self.assertEqual(type(ls.solve()['x']), np.complex64)

        ls = linsolve.LinearSolver({'x_': np.ones(1,dtype=np.complex64)[0]}, sparse=self.sparse)
        self.assertEqual(ls.dtype,np.float32)
        self.assertEqual(type(ls.solve()['x']), np.complex64)

        ls = linsolve.LinearSolver({'x': np.ones(1,dtype=np.complex64)[0]}, sparse=self.sparse)
        self.assertEqual(ls.dtype,np.complex64)
        self.assertEqual(type(ls.solve()['x']), np.complex64)

        ls = linsolve.LinearSolver({'c*x': 1.0}, c=1.0+1.0j, sparse=self.sparse)
        self.assertEqual(ls.dtype,np.complex64)
        self.assertEqual(type(ls.solve()['x']), np.complex64)

        d = {'c*x': np.ones(1,dtype=np.float32)[0]}
        wgts = {'c*x': np.ones(1,dtype=np.float64)[0]}
        c = np.ones(1,dtype=np.float32)[0]
        ls = linsolve.LinearSolver(d, wgts=wgts, c=c, sparse=self.sparse)
        self.assertEqual(ls.dtype,np.float64)
        self.assertEqual(type(ls.solve()['x']), np.float64)

class TestLinearSolverSparse(TestLinearSolver):
    def setUp(self):
        self.sparse = True
        eqs = ['x+y','x-y']
        x,y = 1,2
        d,w = {}, {}
        for eq in eqs: d[eq],w[eq] = eval(eq), 1.
        self.ls = linsolve.LinearSolver(d,w,sparse=self.sparse)



class TestLogProductSolver(unittest.TestCase):
    def setUp(self):
        self.sparse=False
    def test_init(self):
        x,y,z = np.exp(1.), np.exp(2.), np.exp(3.)
        keys = ['x*y*z', 'x*y', 'y*z']
        d,w = {}, {}
        for k in keys: d[k],w[k] = eval(k), 1.
        ls = linsolve.LogProductSolver(d,w,sparse=self.sparse)
        for k in ls.ls_phs.data:
            np.testing.assert_equal(ls.ls_phs.data[k], 0)
        x,y,z = 1.,2.,3.
        for k in ls.ls_amp.data:
            np.testing.assert_equal(eval(k), ls.ls_amp.data[k])
    def test_conj(self):
        x,y = 1+1j, 2+2j
        d,w = {}, {}
        d['x*y_'] = x * y.conjugate()
        d['x_*y'] = x.conjugate() * y
        d['x*y'] = x * y
        d['x_*y_'] = x.conjugate() * y.conjugate()
        for k in d: w[k] = 1.
        ls = linsolve.LogProductSolver(d,w,sparse=self.sparse)
        self.assertEqual(len(ls.ls_amp.data), 4)
        for k in ls.ls_amp.data:
            self.assertEqual(eval(k), 3+3j) # make sure they are all x+y
            self.assertTrue(k.replace('1','-1') in ls.ls_phs.data)
    def test_solve(self):
        x,y,z = np.exp(1.), np.exp(2.), np.exp(3.)
        keys = ['x*y*z', 'x*y', 'y*z']
        d,w = {}, {}
        for k in keys: d[k],w[k] = eval(k), 1.
        ls = linsolve.LogProductSolver(d,w,sparse=self.sparse)
        sol = ls.solve()
        for k in sol:
            self.assertAlmostEqual(sol[k], eval(k))
    def test_conj_solve(self):
        x,y = np.exp(1.), np.exp(2.+1j)
        d,w = {'x*y_':x*y.conjugate(), 'x':x}, {}
        for k in d: w[k] = 1.
        ls = linsolve.LogProductSolver(d,w,sparse=self.sparse)
        sol = ls.solve()
        for k in sol:
            self.assertAlmostEqual(sol[k], eval(k))
    def test_no_abs_phs_solve(self):
        x,y,z = 1.+1j, 2.+2j, 3.+3j
        d,w = {'x*y_':x*y.conjugate(), 'x*z_':x*z.conjugate(), 'y*z_':y*z.conjugate()}, {}
        for k in list(d.keys()): w[k] = 1.
        ls = linsolve.LogProductSolver(d,w,sparse=self.sparse)
        sol = ls.solve()
        x,y,z = sol['x'], sol['y'], sol['z']
        self.assertAlmostEqual(np.angle(x*y.conjugate()), 0.)
        self.assertAlmostEqual(np.angle(x*z.conjugate()), 0.)
        self.assertAlmostEqual(np.angle(y*z.conjugate()), 0.)
        # check projection of degenerate mode
        self.assertAlmostEqual(np.angle(x), 0.)
        self.assertAlmostEqual(np.angle(y), 0.)
        self.assertAlmostEqual(np.angle(z), 0.)
    def test_dtype(self):
        for dtype in (np.float32, np.float64, np.complex64, np.complex128):
            x,y,z = np.exp(1.), np.exp(2.), np.exp(3.)
            keys = ['x*y*z', 'x*y', 'y*z']
            d,w = {}, {}
            for k in keys:
                d[k] = eval(k).astype(dtype)
                w[k] = np.float32(1.)
            ls = linsolve.LogProductSolver(d,w,sparse=self.sparse)
            sol = ls.solve()
            for k in sol:
                self.assertEqual(sol[k].dtype, dtype)

class TestLogProductSolverSparse(TestLogProductSolver):
    def setUp(self):
        self.sparse=True


class TestLinProductSolver(unittest.TestCase):
    def setUp(self):
        self.sparse=False
    def test_init(self):
        x,y,z = 1.+1j, 2.+2j, 3.+3j
        d,w = {'x*y_':x*y.conjugate(), 'x*z_':x*z.conjugate(), 'y*z_':y*z.conjugate()}, {}
        for k in list(d.keys()): w[k] = 1.
        sol0 = {}
        for k in 'xyz': sol0[k] = eval(k)+.01
        ls = linsolve.LinProductSolver(d,sol0,w,sparse=self.sparse)
        x,y,z = 1.,1.,1.
        x_,y_,z_ = 1.,1.,1.
        dx = dy = dz = .001
        dx_ = dy_ = dz_ = .001
        for k in ls.ls.keys:
            self.assertAlmostEqual(eval(k), 0.002)
        self.assertEqual(len(ls.ls.prms), 3)
    def test_real_solve(self):
        x,y,z = 1., 2., 3.
        keys = ['x*y', 'x*z', 'y*z']
        d,w = {}, {}
        for k in keys: d[k],w[k] = eval(k), 1.
        sol0 = {}
        for k in 'xyz': sol0[k] = eval(k)+.01
        ls = linsolve.LinProductSolver(d,sol0,w,sparse=self.sparse)
        sol = ls.solve()
        for k in sol:
            #print sol0[k], sol[k]
            self.assertAlmostEqual(sol[k], eval(k), 4)
    def test_single_term(self):
        x,y,z = 1., 2., 3.
        keys = ['x*y', 'x*z', '2*z']
        d,w = {}, {}
        for k in keys: d[k],w[k] = eval(k), 1.
        sol0 = {}
        for k in 'xyz': sol0[k] = eval(k)+.01
        ls = linsolve.LinProductSolver(d,sol0,w,sparse=self.sparse)
        sol = ls.solve()
        for k in sol:
            self.assertAlmostEqual(sol[k], eval(k), 4)
    def test_complex_solve(self):
        x,y,z = 1+1j, 2+2j, 3+2j
        keys = ['x*y', 'x*z', 'y*z']
        d,w = {}, {}
        for k in keys: d[k],w[k] = eval(k), 1.
        sol0 = {}
        for k in 'xyz': sol0[k] = eval(k)+.01
        ls = linsolve.LinProductSolver(d,sol0,w,sparse=self.sparse)
        sol = ls.solve()
        for k in sol:
            self.assertAlmostEqual(sol[k], eval(k), 4)
    def test_complex_conj_solve(self):
        x,y,z = 1.+1j, 2.+2j, 3.+3j
        #x,y,z = 1., 2., 3.
        d,w = {'x*y_':x*y.conjugate(), 'x*z_':x*z.conjugate(), 'y*z_':y*z.conjugate()}, {}
        for k in list(d.keys()): w[k] = 1.
        sol0 = {}
        for k in 'xyz': sol0[k] = eval(k) + .01
        ls = linsolve.LinProductSolver(d,sol0,w,sparse=self.sparse)
        ls.prm_order = {'x':0,'y':1,'z':2}
        sol = ls.solve()
        x,y,z = sol['x'], sol['y'], sol['z']
        self.assertAlmostEqual(x*y.conjugate(), d['x*y_'], 3)
        self.assertAlmostEqual(x*z.conjugate(), d['x*z_'], 3)
        self.assertAlmostEqual(y*z.conjugate(), d['y*z_'], 3)
    def test_complex_array_solve(self):
        x = np.arange(30, dtype=np.complex); x.shape = (3,10)
        y = np.arange(30, dtype=np.complex); y.shape = (3,10)
        z = np.arange(30, dtype=np.complex); z.shape = (3,10)
        d,w = {'x*y':x*y, 'x*z':x*z, 'y*z':y*z}, {}
        for k in list(d.keys()): w[k] = np.ones(d[k].shape)
        sol0 = {}
        for k in 'xyz': sol0[k] = eval(k) + .01
        ls = linsolve.LinProductSolver(d,sol0,w,sparse=self.sparse)
        ls.prm_order = {'x':0,'y':1,'z':2}
        sol = ls.solve()
        np.testing.assert_almost_equal(sol['x'], x, 2)
        np.testing.assert_almost_equal(sol['y'], y, 2)
        np.testing.assert_almost_equal(sol['z'], z, 2)
    def test_complex_array_NtimesNfreqs1_solve(self):
        x = np.arange(1, dtype=np.complex); x.shape = (1,1)
        y = np.arange(1, dtype=np.complex); y.shape = (1,1)
        z = np.arange(1, dtype=np.complex); z.shape = (1,1)
        d,w = {'x*y':x*y, 'x*z':x*z, 'y*z':y*z}, {}
        for k in list(d.keys()): w[k] = np.ones(d[k].shape)
        sol0 = {}
        for k in 'xyz': sol0[k] = eval(k) + .01
        ls = linsolve.LinProductSolver(d,sol0,w,sparse=self.sparse)
        ls.prm_order = {'x':0,'y':1,'z':2}
        sol = ls.solve()
        np.testing.assert_almost_equal(sol['x'], x, 2)
        np.testing.assert_almost_equal(sol['y'], y, 2)
        np.testing.assert_almost_equal(sol['z'], z, 2)
    def test_sums_of_products(self):
        x = np.arange(1,31)*(1.0+1.0j); x.shape=(10,3) 
        y = np.arange(1,31)*(2.0-3.0j); y.shape=(10,3)
        z = np.arange(1,31)*(3.0-9.0j); z.shape=(10,3)
        w = np.arange(1,31)*(4.0+2.0j); w.shape=(10,3)
        x_,y_,z_,w_ = list(map(np.conjugate,(x,y,z,w)))
        expressions = ['x*y+z*w', '2*x_*y_+z*w-1.0j*z*w', '2*x*w', '1.0j*x + y*z', '-1*x*z+3*y*w*x+y', '2*w_', '2*x_ + 3*y - 4*z']
        data = {}
        for ex in expressions: data[ex] = eval(ex)
        currentSol = {'x':1.1*x, 'y': .9*y, 'z': 1.1*z, 'w':1.2*w}
        for i in range(20):
            testSolve = linsolve.LinProductSolver(data, currentSol,sparse=self.sparse)
            currentSol = testSolve.solve()
        for var in 'wxyz': 
            np.testing.assert_almost_equal(currentSol[var], eval(var), 4) 
    def test_eval(self):
        x = np.arange(1,31)*(1.0+1.0j); x.shape=(10,3) 
        y = np.arange(1,31)*(2.0-3.0j); y.shape=(10,3)
        z = np.arange(1,31)*(3.0-9.0j); z.shape=(10,3)
        w = np.arange(1,31)*(4.0+2.0j); w.shape=(10,3)
        x_,y_,z_,w_ = list(map(np.conjugate,(x,y,z,w)))
        expressions = ['x*y+z*w', '2*x_*y_+z*w-1.0j*z*w', '2*x*w', '1.0j*x + y*z', '-1*x*z+3*y*w*x+y', '2*w_', '2*x_ + 3*y - 4*z']
        data = {}
        for ex in expressions: data[ex] = eval(ex)
        currentSol = {'x':1.1*x, 'y': .9*y, 'z': 1.1*z, 'w':1.2*w}
        for i in range(40):
            testSolve = linsolve.LinProductSolver(data, currentSol,sparse=self.sparse)
            currentSol = testSolve.solve()
        for var in 'wxyz': 
            np.testing.assert_almost_equal(currentSol[var], eval(var), 4)
        result = testSolve.eval(currentSol)
        for eq in data:
            np.testing.assert_almost_equal(data[eq], result[eq], 4)
    def test_chisq(self):
        x = 1.
        d = {'x*y':1, '.5*x*y+.5*x*y':2, 'y':1}
        currentSol = {'x':2.3,'y':.9}
        for i in range(40):
            testSolve = linsolve.LinProductSolver(d, currentSol,sparse=self.sparse)
            currentSol = testSolve.solve()
        chisq = testSolve.chisq(currentSol)
        np.testing.assert_almost_equal(chisq, .5)
    def test_solve_iteratively(self):
        x = np.arange(1,31)*(1.0+1.0j); x.shape=(10,3) 
        y = np.arange(1,31)*(2.0-3.0j); y.shape=(10,3)
        z = np.arange(1,31)*(3.0-9.0j); z.shape=(10,3)
        w = np.arange(1,31)*(4.0+2.0j); w.shape=(10,3)
        x_,y_,z_,w_ = list(map(np.conjugate,(x,y,z,w)))
        expressions = ['x*y+z*w', '2*x_*y_+z*w-1.0j*z*w', '2*x*w', '1.0j*x + y*z', '-1*x*z+3*y*w*x+y', '2*w_', '2*x_ + 3*y - 4*z']
        data = {}
        for ex in expressions: data[ex] = eval(ex)
        currentSol = {'x':1.1*x, 'y': .9*y, 'z': 1.1*z, 'w':1.2*w}
        testSolve = linsolve.LinProductSolver(data, currentSol,sparse=self.sparse)
        meta, new_sol = testSolve.solve_iteratively()
        for var in 'wxyz': 
            np.testing.assert_almost_equal(new_sol[var], eval(var), 4)
    def test_solve_iteratively_dtype(self):
        x = np.arange(1,31)*(1.0+1.0j); x.shape=(10,3) 
        y = np.arange(1,31)*(2.0-3.0j); y.shape=(10,3)
        z = np.arange(1,31)*(3.0-9.0j); z.shape=(10,3)
        w = np.arange(1,31)*(4.0+2.0j); w.shape=(10,3)
        x_,y_,z_,w_ = list(map(np.conjugate,(x,y,z,w)))
        expressions = ['x*y+z*w', '2*x_*y_+z*w-1.0j*z*w', '2*x*w', '1.0j*x + y*z', '-1*x*z+3*y*w*x+y', '2*w_', '2*x_ + 3*y - 4*z']
        data = {}
        for dtype in (np.complex128, np.complex64):
            for ex in expressions: data[ex] = eval(ex).astype(dtype)
            currentSol = {'x':1.1*x, 'y': .9*y, 'z': 1.1*z, 'w':1.2*w}
            currentSol = {k:v.astype(dtype) for k,v in currentSol.items()}
            testSolve = linsolve.LinProductSolver(data, currentSol,sparse=self.sparse)
            meta, new_sol = testSolve.solve_iteratively()
            for var in 'wxyz':
                self.assertEqual(new_sol[var].dtype, dtype)
                np.testing.assert_almost_equal(new_sol[var], eval(var), 4)

class TestLinProductSolverSparse(TestLinProductSolver):
    def setUp(self):
        self.sparse=True



if __name__ == '__main__':
    unittest.main()
