use std::str::FromStr;
use std::fmt::Debug;
use std::rc::Rc;
use std::cell::RefCell;
use std::io::Read;

#[derive(Debug, Clone)]
pub struct LilValue<T: Clone> {
    pub l: usize,
    pub d: Option<T>
}

#[derive(Debug)]
pub struct HashEntry<T> {
    pub k: String,
    pub v: Option<T>,
}

#[derive(Debug, Clone)]
pub struct HashCell<T> {
    pub e: Vec<Rc<RefCell<HashEntry<T>>>>,
    pub c: usize,
}

#[derive(Debug)]
pub struct HashMap<T> {
    pub cell: Vec<HashCell<T>>,
}

pub const HASHMAP_CELLMASK: u64 = 0xFF;

#[derive(Debug, Clone)]
pub struct LilList<T: Clone> {
    pub items: Vec<Rc<RefCell<LilValue<T>>>>,
}

#[derive(Debug)]
pub struct LilFunc<T: Clone> {
    pub name: String,
    pub code: LilValue<T>,
    pub argnames: LilList<T>,
    pub proc: Option<LilFuncProc<T>>,
}

pub type LilFuncProc<T> = fn(&LilStruct<T>, &str, &[LilValue<T>]) -> LilValue<T>;
pub type LilCallbackProc<T> = fn(&LilStruct<T>, &str, &[LilValue<T>]) -> LilValue<T>;
pub const CALLBACKS: usize = 16;

pub struct LilStruct<T: Clone> {
    pub code: String,
    pub rootcode: String,
    pub clen: usize,
    pub head: usize,
    pub ignoreeol: i32,
    pub cmd: Vec<Rc<RefCell<LilFunc<T>>>>,
    pub cmds: usize,
    pub syscmds: usize,
    pub cmdmap: HashMap<Rc<RefCell<LilFunc<T>>>>,
    pub catcher: String,
    pub in_catcher: i32,
    pub dollarprefix: String,
    pub env: Rc<RefCell<LilEnv<T>>>,
    pub rootenv: Rc<RefCell<LilEnv<T>>>,
    pub downenv: Rc<RefCell<LilEnv<T>>>,
    pub empty: LilValue<T>,
    pub error: i32,
    pub err_head: usize,
    pub err_msg: String,
    pub callback: [LilCallbackProc<T>; CALLBACKS],
    pub parse_depth: usize,
    pub data: T,
    pub embed: String,
    pub embedlen: usize,
}

#[derive(Debug, Clone)]
pub struct LilVar<T: Clone> {
    pub n: String,
    pub w: String,
    pub env: Rc<RefCell<LilEnv<T>>>,
    pub v: LilValue<T>,
}

#[derive(Debug)]
pub struct LilEnv<T: Clone> {
    pub parent: Option<Rc<RefCell<LilEnv<T>>>>,
    pub func: Option<Rc<RefCell<LilFunc<T>>>>,
    pub catcher_for: LilValue<T>,
    pub var: Vec<Rc<RefCell<LilVar<T>>>>,
    pub vars: usize,
    pub varmap: HashMap<Rc<RefCell<LilVar<T>>>>,
    pub retval: LilValue<T>,
    pub retval_set: bool,
    pub breakrun: bool,
}

pub static mut listpool: Vec<Rc<RefCell<LilList<()>>>> = Vec::new();
pub static mut listpoolsize: usize = 0;
pub static mut listpoolcap: usize = 0;

#[derive(Debug, Clone)]
pub enum ExprEvalType {
    Int,
    Float,
}

#[derive(Debug, Clone)]
pub struct Expreval {
    pub type_: ExprEvalType,
    pub ival: i64,
    pub dval: f64,
    pub head: usize,
    pub len: usize,
    pub code: String,
}

pub fn hm_hash(key: &str) -> u64 {
    let mut hash: u64 = 5381;
    for c in key.bytes() {
        hash = ((hash << 5) + hash) + c as u64;
    }
    hash
}

pub fn alloc_value_len<T: Clone + FromStr>(str: Option<String>, len: usize) -> Option<LilValue<T>> 
where
    <T as FromStr>::Err: Debug
{
    let mut val = LilValue {
        l: 0,
        d: None
    };

    if let Some(s) = str {
        val.l = len;
        val.d = Some(s.parse().unwrap());
    } else {
        val.l = 0;
        val.d = None;
    }

    Some(val)
}

pub fn hm_get<T: Clone + Debug>(hm: &HashMap<T>, key: &str) -> Option<T> {
    let cell = &hm.cell[(hm_hash(key) & HASHMAP_CELLMASK) as usize];
    for i in 0..cell.c {
        if key == cell.e[i].borrow().k {
            return cell.e[i].borrow().v.clone();
        }
    }
    None
}

pub fn lil_free_value<T: Clone>(val: Option<Rc<RefCell<LilValue<T>>>>) {
    if val.is_none() {
        return;
    }
    let val = val.unwrap();
    let mut val = val.borrow_mut();
    val.d = None;
}

pub fn strclone(s: &str) -> Option<String> {
    let mut ns = String::with_capacity(s.len() + 1);
    ns.push_str(s);
    Some(ns)
}

pub fn alloc_value<T: Clone + FromStr>(str: Option<String>) -> Option<LilValue<T>> 
where
    <T as FromStr>::Err: Debug
{
    let len = str.as_ref().map_or(0, |s| s.len());
    alloc_value_len(str, len)
}

pub fn find_cmd<T: Clone>(lil: &LilStruct<T>, name: &str) -> Option<Rc<RefCell<LilFunc<T>>>> {
    None
}

pub fn lil_free_list<T: Clone>(_list: LilList<T>) {}

pub fn hm_put<T>(map: &mut HashMap<T>, key: &str, value: Option<T>) {
}

pub fn lil_append_val<T: Clone>(val: &mut LilValue<T>, v: &LilValue<T>) -> i32 {
    if v.d.is_none() || v.l == 0 {
        return 1;
    }

    match (&mut val.d, &v.d) {
        (Some(val_data), Some(v_data)) => {
            let mut new_data = val_data.clone();
            new_data = v_data.clone();
            val.d = Some(new_data);
            val.l += v.l;
            1
        }
        _ => 1,
    }
}

pub fn ateol<T: Clone>(lil: &LilStruct<T>) -> bool {
    !(lil.ignoreeol != 0) && (lil.code.chars().nth(lil.head) == Some('\n') || lil.code.chars().nth(lil.head) == Some('\r') || lil.code.chars().nth(lil.head) == Some(';'))
}

pub fn lil_append_char<T: Clone + Debug + FromStr>(val: Rc<RefCell<LilValue<T>>>, ch: char) -> i32 {
    let mut val = val.borrow_mut();
    if let Some(ref mut data) = val.d {
        let mut s = format!("{:?}", data);
        s.push(ch);
        val.d = s.parse().ok();
        val.l = s.len();
        1
    } else {
        let s = ch.to_string();
        val.d = s.parse().ok();
        val.l = s.len();
        1
    }
}

pub fn islilspecial(ch: i8) -> i32 {
    (ch == b'$' as i8 || ch == b'{' as i8 || ch == b'}' as i8 || ch == b'[' as i8 || ch == b']' as i8 || ch == b'"' as i8 || ch == b'\'' as i8 || ch == b';' as i8) as i32
}

pub fn skip_spaces<T: Clone>(lil: &mut LilStruct<T>) {
    while lil.head < lil.clen {
        let current_char = lil.code.chars().nth(lil.head).unwrap();
        if current_char == '#' {
            if lil.code.chars().nth(lil.head + 1) == Some('#') && lil.code.chars().nth(lil.head + 2) != Some('#') {
                lil.head += 2;
                while lil.head < lil.clen {
                    let current_char = lil.code.chars().nth(lil.head).unwrap();
                    if current_char == '#' && lil.code.chars().nth(lil.head + 1) == Some('#') && lil.code.chars().nth(lil.head + 2) != Some('#') {
                        lil.head += 2;
                        break;
                    }
                    lil.head += 1;
                }
            } else {
                while lil.head < lil.clen && !ateol(lil) {
                    lil.head += 1;
                }
            }
        } else if current_char == '\\' && (lil.code.chars().nth(lil.head + 1) == Some('\r') || lil.code.chars().nth(lil.head + 1) == Some('\n')) {
            lil.head += 1;
            while lil.head < lil.clen && ateol(lil) {
                lil.head += 1;
            }
        } else if current_char == '\r' || current_char == '\n' {
            if lil.ignoreeol != 0 {
                lil.head += 1;
            } else {
                break;
            }
        } else if current_char.is_whitespace() {
            lil.head += 1;
        } else {
            break;
        }
    }
}

pub fn hm_destroy<T>(hm: &mut HashMap<T>) {
    for cell in hm.cell.iter_mut() {
        cell.e.clear();
        cell.c = 0;
    }
}

pub fn lil_find_local_var<T: Clone + Debug>(lil: &LilStruct<T>, env: &LilEnv<T>, name: &str) -> Option<Rc<RefCell<LilVar<T>>>> {
    hm_get(&env.varmap, name)
}

pub fn lil_append_string_len<T: Clone + Debug + From<String> + AsRef<str> + AsMut<String>>(val: &mut LilValue<T>, s: &str, len: usize) -> i32 {
    if s.is_empty() {
        return 1;
    }

    let s_slice = if len < s.len() { &s[..len] } else { s };
    
    match &mut val.d {
        Some(data) => {
            let str_data = data.as_mut();
            str_data.push_str(s_slice);
            val.l += s_slice.len();
            1
        },
        None => {
            val.d = Some(T::from(s_slice.to_string()));
            val.l = s_slice.len();
            1
        }
    }
}

pub fn add_func<T: Clone + Debug>(lil: &mut LilStruct<T>, name: &str) -> Option<Rc<RefCell<LilFunc<T>>>> {
    let cmd = find_cmd(lil, name);
    if let Some(cmd) = cmd {
        let mut cmd_ref = cmd.borrow_mut();
        if cmd_ref.argnames.items.len() > 0 {
            let argnames = cmd_ref.argnames.clone();
            lil_free_list(argnames);
        }
        lil_free_value(Some(Rc::new(RefCell::new(cmd_ref.code.clone()))));
        cmd_ref.argnames = LilList { items: Vec::new() };
        cmd_ref.code = LilValue { l: 0, d: None };
        cmd_ref.proc = None;
        return Some(Rc::clone(&cmd));
    }
    let new_cmd = Rc::new(RefCell::new(LilFunc {
        name: strclone(name).unwrap(),
        code: LilValue { l: 0, d: None },
        argnames: LilList { items: Vec::new() },
        proc: None,
    }));
    lil.cmd.push(Rc::clone(&new_cmd));
    lil.cmds += 1;
    hm_put(&mut lil.cmdmap, name, Some(Rc::clone(&new_cmd)));
    Some(new_cmd)
}

pub fn lil_alloc_env<T: Clone>(parent: Option<Rc<RefCell<LilEnv<T>>>>) -> Rc<RefCell<LilEnv<T>>> {
    let env = Rc::new(RefCell::new(LilEnv {
        parent,
        func: None,
        catcher_for: LilValue { l: 0, d: None },
        var: Vec::new(),
        vars: 0,
        varmap: HashMap {
            cell: (0..256).map(|_| HashCell { e: Vec::new(), c: 0 }).collect(),
        },
        retval: LilValue { l: 0, d: None },
        retval_set: false,
        breakrun: false,
    }));
    env
}

pub fn lil_list_append<T: Clone>(_list: &mut LilList<T>, _val: LilValue<T>) {}

pub fn lil_alloc_list<T: Clone>() -> LilList<T> {
    LilList { items: Vec::new() }
}

pub fn lil_free_env<T: Clone>(env: Option<Rc<RefCell<LilEnv<T>>>>) {
    if env.is_none() {
        return;
    }
    let env = env.unwrap();
    let mut env = env.borrow_mut();
    lil_free_value(Some(Rc::new(RefCell::new(env.retval.clone()))));
    hm_destroy(&mut env.varmap);
    for i in 0..env.vars {
        let var = env.var[i].borrow_mut();
        lil_free_value(Some(Rc::new(RefCell::new(var.v.clone()))));
    }
    env.var.clear();
    env.vars = 0;
}

pub fn lil_find_var<T: Clone>(_lil: &LilStruct<T>, _env: Rc<RefCell<LilEnv<T>>>, _name: &str) -> Option<Rc<RefCell<LilVar<T>>>> {
    None
}

pub fn lil_clone_value<T: Clone>(val: &LilValue<T>) -> LilValue<T> {
    val.clone()
}

pub fn lil_to_string<T: Clone>(value: &LilValue<T>) -> String {
    String::new()
}

pub fn needs_escape(str: &str) -> i32 {
    if str.is_empty() {
        return 1;
    }
    for c in str.chars() {
        if c.is_ascii_punctuation() || c.is_whitespace() {
            return 1;
        }
    }
    0
}

pub fn lil_append_string<T: Clone + Debug + From<String> + AsRef<str> + AsMut<String>>(val: &mut LilValue<T>, s: &str) -> i32 {
    lil_append_string_len(val, s, s.len())
}

pub fn fnc_exit<T: Clone>(lil: Rc<RefCell<LilStruct<T>>>, argc: usize, argv: Vec<Rc<RefCell<LilValue<T>>>>) -> Option<Rc<RefCell<LilValue<T>>>> {
    let lil_ref = lil.borrow();
    if let Some(proc) = lil_ref.callback.get(0) {
        let arg = if argc > 0 { Some(argv[0].clone()) } else { None };
        let lil_wrap = &*lil_ref;
        proc(lil_wrap, "", &[]);
    }
    None
}

pub fn fnc_return<T: Clone>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    lil.env.borrow_mut().breakrun = true;
    lil.env.borrow_mut().retval = if argc < 1 { LilValue { l: 0, d: None } } else { argv[0].clone() };
    lil.env.borrow_mut().retval_set = true;
    if argc < 1 { LilValue { l: 0, d: None } } else { argv[0].clone() }
}

pub fn fnc_expr<T: Clone>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn lil_eval_expr_wrap<T: Clone>(lil: &LilStruct<T>, val: &LilValue<T>) -> LilValue<T> {
        LilValue { l: 0, d: None }
    }
    fn alloc_value_wrap<T: Clone>(d: Option<T>) -> LilValue<T> {
        LilValue { l: 0, d }
    }
    fn lil_append_char_wrap<T: Clone>(val: &mut LilValue<T>, c: char) {}
    fn lil_append_val_wrap<T: Clone>(val: &mut LilValue<T>, v: &LilValue<T>) {}
    fn lil_free_value_wrap<T: Clone>(val: LilValue<T>) {}

    if argc == 1 {
        return lil_eval_expr_wrap(lil, &argv[0]);
    }
    if argc > 1 {
        let mut val = alloc_value_wrap::<T>(None);
        let mut r;
        for i in 0..argc {
            if i != 0 {
                lil_append_char_wrap(&mut val, ' ');
            }
            lil_append_val_wrap(&mut val, &argv[i]);
        }
        r = lil_eval_expr_wrap(lil, &val);
        lil_free_value_wrap(val);
        return r;
    }
    LilValue { l: 0, d: None }
}

pub fn fnc_repstr<T: Clone + FromStr + Debug>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn lil_to_string<T: Clone + Debug>(value: &LilValue<T>) -> String {
        match &value.d {
            Some(v) => format!("{:?}", v),
            None => String::new(),
        }
    }

    fn lil_alloc_string<T: Clone>(s: &str) -> LilValue<T> {
        LilValue {
            l: s.len(),
            d: None,
        }
    }

    if argc < 1 {
        return LilValue { l: 0, d: None };
    }
    if argc < 3 {
        return argv[0].clone();
    }

    let from = lil_to_string(&argv[1]);
    let to = lil_to_string(&argv[2]);
    if from.is_empty() {
        return LilValue { l: 0, d: None };
    }

    let mut src = lil_to_string(&argv[0]);
    let from_len = from.len();
    let to_len = to.len();

    while let Some(idx) = src.find(&from) {
        let mut new_src = String::with_capacity(src.len() - from_len + to_len);
        new_src.push_str(&src[..idx]);
        new_src.push_str(&to);
        new_src.push_str(&src[idx + from_len..]);
        src = new_src;
    }

    lil_alloc_string(&src)
}

pub fn fnc_reflect<T: Clone + Debug + From<String> + From<&'static str> + From<i64> + ToString>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> Option<LilValue<T>> {
    if argc == 0 { return None; }
    let type_str = lil_to_string(&argv[0]);
    match type_str.as_str() {
        "version" => Some(LilValue { l: 3, d: Some("0.1".into()) }),
        "args" => {
            if argc < 2 { return None; }
            let func_name = lil_to_string(&argv[1]);
            let func = find_cmd(lil, &func_name);
            if func.is_none() || func.as_ref().unwrap().borrow().argnames.items.is_empty() { return None; }
            Some(func.unwrap().borrow().argnames.items[0].borrow().clone())
        },
        "body" => {
            if argc < 2 { return None; }
            let func_name = lil_to_string(&argv[1]);
            let func = find_cmd(lil, &func_name);
            if func.is_none() || func.as_ref().unwrap().borrow().proc.is_some() { return None; }
            Some(func.unwrap().borrow().code.clone())
        },
        "func-count" => Some(LilValue { l: 0, d: Some((lil.cmds as i64).into()) }),
        "funcs" => {
            let mut funcs = LilList { items: Vec::<Rc<RefCell<LilValue<T>>>>::new() };
            for i in 0..lil.cmds {
                funcs.items.push(Rc::new(RefCell::new(LilValue { l: lil.cmd[i].borrow().name.len(), d: Some(lil.cmd[i].borrow().name.clone().into()) })));
            }
            Some(LilValue { l: funcs.items.len(), d: None })
        },
        "vars" => {
            let mut vars = LilList { items: Vec::<Rc<RefCell<LilValue<T>>>>::new() };
            let mut current_env = Some(lil.env.clone());
            while let Some(e) = current_env {
                for i in 0..e.borrow().vars {
                    vars.items.push(Rc::new(RefCell::new(LilValue { l: e.borrow().var[i].borrow().n.len(), d: Some(e.borrow().var[i].borrow().n.clone().into()) })));
                }
                current_env = e.borrow().parent.as_ref().map(|p| p.clone());
            }
            Some(LilValue { l: vars.items.len(), d: None })
        },
        "globals" => {
            let mut vars = LilList { items: Vec::<Rc<RefCell<LilValue<T>>>>::new() };
            for i in 0..lil.rootenv.borrow().vars {
                vars.items.push(Rc::new(RefCell::new(LilValue { l: lil.rootenv.borrow().var[i].borrow().n.len(), d: Some(lil.rootenv.borrow().var[i].borrow().n.clone().into()) })));
            }
            Some(LilValue { l: vars.items.len(), d: None })
        },
        "has-func" => {
            if argc == 1 { return None; }
            let target = lil_to_string(&argv[1]);
            if lil.cmdmap.cell.iter().any(|cell| cell.e.iter().any(|entry| entry.borrow().k == target)) {
                Some(LilValue { l: 1, d: Some("1".into()) })
            } else {
                None
            }
        },
        "has-var" => {
            if argc == 1 { return None; }
            let target = lil_to_string(&argv[1]);
            let mut current_env = Some(lil.env.clone());
            while let Some(e) = current_env {
                if e.borrow().varmap.cell.iter().any(|cell| cell.e.iter().any(|entry| entry.borrow().k == target)) {
                    return Some(LilValue { l: 1, d: Some("1".into()) });
                }
                current_env = e.borrow().parent.as_ref().map(|p| p.clone());
            }
            None
        },
        "has-global" => {
            if argc == 1 { return None; }
            let target = lil_to_string(&argv[1]);
            for i in 0..lil.rootenv.borrow().vars {
                if target == lil.rootenv.borrow().var[i].borrow().n { 
                    return Some(LilValue { l: 1, d: Some("1".into()) });
                }
            }
            None
        },
        "error" => lil.err_msg.is_empty().then(|| LilValue { l: lil.err_msg.len(), d: Some(lil.err_msg.clone().into()) }),
        "dollar-prefix" => {
            if argc == 1 { return Some(LilValue { l: lil.dollarprefix.len(), d: Some(lil.dollarprefix.clone().into()) }); }
            let r = LilValue { l: lil.dollarprefix.len(), d: Some(lil.dollarprefix.clone().into()) };
            lil.dollarprefix = lil_to_string(&argv[1]);
            Some(r)
        },
        "this" => {
            let mut current_env = Some(lil.env.clone());
            let mut result_env = None;
            while let Some(e) = current_env {
                if e.borrow().catcher_for.d.is_some() || e.borrow().func.is_some() {
                    result_env = Some(e);
                    break;
                }
                current_env = e.borrow().parent.as_ref().map(|p| p.clone());
            }
            if let Some(e) = result_env {
                if e.borrow().catcher_for.d.is_some() { return Some(LilValue { l: lil.catcher.len(), d: Some(lil.catcher.clone().into()) }); }
                if Rc::ptr_eq(&e, &lil.rootenv) { return Some(LilValue { l: lil.rootcode.len(), d: Some(lil.rootcode.clone().into()) }); }
                if let Some(func) = &e.borrow().func { return Some(func.borrow().code.clone()); }
            }
            None
        },
        "name" => {
            let mut current_env = Some(lil.env.clone());
            let mut result_env = None;
            while let Some(e) = current_env {
                if e.borrow().catcher_for.d.is_some() || e.borrow().func.is_some() {
                    result_env = Some(e);
                    break;
                }
                current_env = e.borrow().parent.as_ref().map(|p| p.clone());
            }
            if let Some(e) = result_env {
                if e.borrow().catcher_for.d.is_some() { return Some(e.borrow().catcher_for.clone()); }
                if Rc::ptr_eq(&e, &lil.rootenv) { return None; }
                if let Some(func) = &e.borrow().func { return Some(LilValue { l: func.borrow().name.len(), d: Some(func.borrow().name.clone().into()) }); }
            }
            None
        },
        _ => None
    }
}

pub fn lil_alloc_string(s: Option<String>) -> Option<LilValue<String>> {
    s.map(|s| LilValue { l: s.len(), d: Some(s) })
}

pub fn lil_alloc_integer<T: Clone + From<i64>>(i: i64) -> LilValue<T> {
    LilValue { l: 0, d: Some(i.into()) }
}

pub fn lil_list_to_value<T: Clone>(_list: &LilList<T>, _flag: i32) -> LilValue<T> {
    LilValue { l: 0, d: None }
}

pub fn hm_has<T>(map: &HashMap<T>, _key: &str) -> bool {
    false
}

pub fn fnc_indexof<T: Clone + PartialEq + Debug>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> Option<LilValue<T>> {
    if argc < 2 {
        return None;
    }

    fn lil_subst_to_list_wrap<T: Clone>(_: &LilStruct<T>, _: &LilValue<T>) -> LilList<T> {
        LilList { items: Vec::new() }
    }
    fn lil_to_string_wrap<T: Clone + Debug>(_: &Rc<RefCell<LilValue<T>>>) -> String {
        String::new()
    }
    fn lil_alloc_integer_wrap<T: Clone>(index: i32) -> LilValue<T> {
        LilValue { l: index as usize, d: None }
    }
    fn lil_free_list_wrap<T: Clone>(_: LilList<T>) {}

    let list = lil_subst_to_list_wrap(lil, &argv[0]);
    let mut result = None;

    for (index, item) in list.items.iter().enumerate() {
        let item_str = lil_to_string_wrap(item);
        let arg_str = lil_to_string_wrap(&Rc::new(RefCell::new(argv[1].clone())));
        if item_str == arg_str {
            result = Some(lil_alloc_integer_wrap(index as i32));
            break;
        }
    }

    lil_free_list_wrap(list);
    result
}

pub fn fnc_rand<T: Clone + From<f64>>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    LilValue {
        l: 8,
        d: Some(0.5f64.into())
    }
}

pub fn fnc_foreach<T: Clone + Debug + ToString>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn lil_subst_to_list_wrap<T: Clone>(_lil: &LilStruct<T>, _val: &LilValue<T>) -> LilList<T> {
        LilList { items: Vec::new() }
    }
    fn lil_set_var_wrap<T: Clone>(_lil: &mut LilStruct<T>, _name: &str, _val: Rc<RefCell<LilValue<T>>>, _flags: i32) {}
    fn lil_parse_value_wrap<T: Clone>(_lil: &mut LilStruct<T>, _val: &LilValue<T>, _flags: i32) -> LilValue<T> {
        LilValue { l: 0, d: None }
    }
    fn lil_list_to_value_wrap<T: Clone>(_list: &LilList<T>, _flags: i32) -> LilValue<T> {
        LilValue { l: 0, d: None }
    }

    let mut rlist = LilList { items: Vec::new() };
    let mut listidx = 0;
    let mut codeidx = 1;
    let mut varname = "i".to_string();
    if argc < 2 { return LilValue { l: 0, d: None }; }
    if argc >= 3 {
        varname = argv[0].d.as_ref().unwrap().to_string();
        listidx = 1;
        codeidx = 2;
    }
    let list = lil_subst_to_list_wrap(lil, &argv[listidx]);
    for i in 0..list.items.len() {
        let item = list.items[i].clone();
        lil_set_var_wrap(lil, &varname, item, 3);
        let rv = lil_parse_value_wrap(lil, &argv[codeidx], 0);
        if rv.l != 0 {
            rlist.items.push(Rc::new(RefCell::new(rv)));
        }
        if lil.env.borrow().breakrun || lil.error != 0 { break; }
    }
    let r = lil_list_to_value_wrap(&rlist, 1);
    r
}

pub fn fnc_subst<T: Clone>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> Option<LilValue<T>> {
    if argc < 1 {
        return None;
    }
    fn lil_subst_to_value_wrap<T: Clone>(lil: &LilStruct<T>, val: &LilValue<T>) -> LilValue<T> {
        val.clone()
    }
    Some(lil_subst_to_value_wrap(lil, &argv[0]))
}

pub fn fnc_jaileval<T: Clone + Debug + ToString>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> Option<LilValue<T>> {
    fn lil_to_string_wrap<T: Clone + ToString>(val: &LilValue<T>) -> String {
        match &val.d {
            Some(v) => v.to_string(),
            None => String::new(),
        }
    }

    fn lil_register_wrap<T: Clone>(_lil: &mut LilStruct<T>, _name: &str, _proc: LilFuncProc<T>) {}

    fn lil_parse_value_wrap<T: Clone>(_lil: &mut LilStruct<T>, _val: &LilValue<T>, _depth: usize) -> Option<LilValue<T>> {
        None
    }

    let mut base = 0;
    if argc == 0 {
        return None;
    }
    if lil_to_string_wrap(&argv[0]) == "clean" {
        base = 1;
        if argc == 1 {
            return None;
        }
    }
    let mut sublil = LilStruct {
        code: String::new(),
        rootcode: String::new(),
        clen: 0,
        head: 0,
        ignoreeol: 0,
        cmd: Vec::new(),
        cmds: 0,
        syscmds: 0,
        cmdmap: HashMap { cell: Vec::new() },
        catcher: String::new(),
        in_catcher: 0,
        dollarprefix: String::new(),
        env: Rc::new(RefCell::new(LilEnv {
            parent: None,
            func: None,
            catcher_for: LilValue { l: 0, d: None },
            var: Vec::new(),
            vars: 0,
            varmap: HashMap { cell: Vec::new() },
            retval: LilValue { l: 0, d: None },
            retval_set: false,
            breakrun: false,
        })),
        rootenv: Rc::new(RefCell::new(LilEnv {
            parent: None,
            func: None,
            catcher_for: LilValue { l: 0, d: None },
            var: Vec::new(),
            vars: 0,
            varmap: HashMap { cell: Vec::new() },
            retval: LilValue { l: 0, d: None },
            retval_set: false,
            breakrun: false,
        })),
        downenv: Rc::new(RefCell::new(LilEnv {
            parent: None,
            func: None,
            catcher_for: LilValue { l: 0, d: None },
            var: Vec::new(),
            vars: 0,
            varmap: HashMap { cell: Vec::new() },
            retval: LilValue { l: 0, d: None },
            retval_set: false,
            breakrun: false,
        })),
        empty: LilValue { l: 0, d: None },
        error: 0,
        err_head: 0,
        err_msg: String::new(),
        callback: [|_, _, _| LilValue { l: 0, d: None }; CALLBACKS],
        parse_depth: 0,
        data: argv[0].d.as_ref().unwrap().clone(),
        embed: String::new(),
        embedlen: 0,
    };
    if base != 1 {
        for i in lil.syscmds..lil.cmds {
            let fnc = lil.cmd[i].clone();
            if fnc.borrow().proc.is_none() {
                continue;
            }
            lil_register_wrap(&mut sublil, &fnc.borrow().name, fnc.borrow().proc.unwrap());
        }
    }
    let r = lil_parse_value_wrap(&mut sublil, &argv[base], 1);
    r
}

pub fn lil_register<T: Clone>(lil: &mut LilStruct<T>, name: &str, proc: LilFuncProc<T>) {
    let func = Rc::new(RefCell::new(LilFunc {
        name: name.to_string(),
        code: LilValue { l: 0, d: None },
        argnames: LilList { items: Vec::new() },
        proc: Some(proc),
    }));
    lil.cmd.push(func.clone());
    lil.cmds += 1;
}

pub fn lil_parse_value<T: Clone>(lil: &mut LilStruct<T>, val: &LilValue<T>, depth: usize) -> Option<LilValue<T>> {
    Some(val.clone())
}

pub fn fnc_concat<T: Clone + From<String>>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    let mut r = LilValue { l: 0, d: Some(String::new().into()) };
    if argc < 1 { return r; }
    for i in 0..argc {
        let list = argv[i].clone();
        let tmp = list;
        lil_append_val_wrap(&mut r, tmp);
    }
    r
}

fn lil_append_val_wrap<T: Clone>(dst: &mut LilValue<T>, src: LilValue<T>) {
    if let Some(d) = &mut dst.d {
        if let Some(s) = src.d {
            *d = s;
        }
    }
}

pub fn fnc_set<T: Clone + ToString>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> Option<LilValue<T>> {
    fn lil_get_var_wrap<T: Clone>(lil: &LilStruct<T>, name: &str) -> Option<Rc<RefCell<LilVar<T>>>> {
        None
    }
    fn lil_set_var_wrap<T: Clone>(lil: &LilStruct<T>, name: &str, value: &LilValue<T>, access: i32) -> Option<Rc<RefCell<LilVar<T>>>> {
        None
    }

    let mut i = 0;
    let mut var: Option<Rc<RefCell<LilVar<T>>>> = None;
    let mut access = 1;
    if argc == 0 { return None; }
    if argv[0].d.as_ref().map_or(false, |d| d.to_string() == "global") {
        i = 1;
        access = 0;
    }
    while i < argc {
        if argc == i + 1 {
            return lil_get_var_wrap(lil, &argv[i].d.as_ref()?.to_string()).map(|v| v.borrow().v.clone());
        }
        var = lil_set_var_wrap(lil, &argv[i].d.as_ref()?.to_string(), &argv[i + 1], access);
        i += 2;
    }
    var.map(|v| v.borrow().v.clone())
}

pub fn fnc_char<T: Clone + From<String> + FromStr + Debug>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    if argc == 0 {
        return LilValue { l: 0, d: None };
    }
    let s = match &argv[0].d {
        Some(val) => {
            let mut buf = [0u8; 2];
            buf[0] = format!("{:?}", val).parse::<u8>().unwrap_or(0);
            buf[1] = 0;
            String::from_utf8_lossy(&buf).to_string()
        },
        None => String::new(),
    };
    LilValue { l: s.len(), d: Some(T::from(s)) }
}

pub fn fnc_while<T: Clone + ToString>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> Option<LilValue<T>> {
    let mut r: Option<LilValue<T>> = None;
    let mut base = 0;
    let mut not = false;
    if argc < 1 { return None; }
    if lil_to_string(&argv[0]) == "not" {
        base = 1;
        not = true;
    }
    if argc < base + 2 { return None; }
    while lil.error == 0 && !lil.env.borrow().breakrun {
        let val = lil_eval_expr(lil, &argv[base]);
        if val.is_none() || lil.error != 0 { return None; }
        let mut v = lil_to_boolean(&val.unwrap());
        if not { v = !v; }
        if !v {
            break;
        }
        if r.is_some() {
            r = None;
        }
        r = lil_parse_value(lil, &argv[base + 1], 0);
    }
    r
}

pub fn lil_eval_expr<T: Clone>(_lil: &LilStruct<T>, _val: &LilValue<T>) -> Option<LilValue<T>> {
    None
}

pub fn lil_to_boolean<T: Clone>(_val: &LilValue<T>) -> bool {
    false
}

pub fn fnc_topeval<T: Clone>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn fnc_eval_wrap<T: Clone>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
        LilValue { l: 0, d: None }
    }
    let thisenv = Rc::clone(&lil.env);
    let thisdownenv = Rc::clone(&lil.downenv);
    lil.env = Rc::clone(&lil.rootenv);
    lil.downenv = Rc::clone(&thisenv);
    let r = fnc_eval_wrap(lil, argc, argv);
    lil.downenv = thisdownenv;
    lil.env = thisenv;
    r
}

pub fn fnc_error<T: Clone + std::fmt::Display>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    let err_msg = if argc > 0 {
        match &argv[0].d {
            Some(d) => d.to_string(),
            None => String::new(),
        }
    } else {
        String::new()
    };
    lil.error = 1;
    lil.err_msg = err_msg;
    LilValue { l: 0, d: None }
}

pub fn fnc_strcmp<T: Clone + ToString>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn lil_to_string_wrap<T: Clone + ToString>(value: &LilValue<T>) -> String {
        match &value.d {
            Some(v) => v.to_string(),
            None => String::new(),
        }
    }
    if argc < 2 {
        return LilValue { l: 0, d: None };
    }
    let s1 = lil_to_string_wrap(&argv[0]);
    let s2 = lil_to_string_wrap(&argv[1]);
    LilValue { l: s1.cmp(&s2) as usize, d: None }
}

pub fn fnc_list<T: Clone>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    let mut list = LilList { items: Vec::new() };
    for i in 0..argc {
        list.items.push(Rc::new(RefCell::new(argv[i].clone())));
    }
    LilValue { l: list.items.len(), d: None }
}

pub fn fnc_if<T: Clone + ToString>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> Option<LilValue<T>> {
    let mut base = 0;
    let mut not = false;
    if argc < 1 { return None; }
    if argv[0].d.as_ref().map_or(false, |s| s.to_string() == "not") {
        base = 1;
        not = true;
    }
    if argc < base + 2 { return None; }
    let val = lil_eval_expr(lil, &argv[base]);
    if val.is_none() || lil.error != 0 { return None; }
    let v = lil_to_boolean(&val.unwrap());
    let v = if not { !v } else { v };
    if v {
        lil_parse_value(lil, &argv[base + 1], 0)
    } else if argc > base + 2 {
        lil_parse_value(lil, &argv[base + 2], 0)
    } else {
        None
    }
}

pub fn fnc_for<T: Clone>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn lil_parse_value_wrap<T: Clone>(lil: &mut LilStruct<T>, val: &LilValue<T>, depth: usize) -> LilValue<T> {
        LilValue { l: 0, d: None }
    }
    fn lil_eval_expr_wrap<T: Clone>(lil: &mut LilStruct<T>, val: &LilValue<T>) -> LilValue<T> {
        LilValue { l: 0, d: None }
    }
    fn lil_to_boolean_wrap<T: Clone>(val: &LilValue<T>) -> bool {
        false
    }

    let mut r = LilValue { l: 0, d: None };
    if argc < 4 { return LilValue { l: 0, d: None }; }
    let _ = lil_parse_value_wrap(lil, &argv[0], 0);
    while lil.error == 0 && !lil.env.borrow().breakrun {
        let val = lil_eval_expr_wrap(lil, &argv[1]);
        if val.l == 0 || lil.error != 0 { return LilValue { l: 0, d: None }; }
        if !lil_to_boolean_wrap(&val) {
            break;
        }
        r = lil_parse_value_wrap(lil, &argv[3], 0);
        let _ = lil_parse_value_wrap(lil, &argv[2], 0);
    }
    r
}

pub fn fnc_split<T: Clone + ToString + From<String>>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    let mut list = LilList::<T> { items: Vec::new() };
    let mut sep = " ".to_string();
    if argc == 0 { return LilValue { l: 0, d: None }; }
    if argc > 1 {
        sep = argv[1].d.as_ref().map(|x| x.to_string()).unwrap_or_else(|| " ".to_string());
        if sep.is_empty() { return argv[0].clone(); }
    }
    let mut val = LilValue { l: 0, d: Some("".to_string().into()) };
    let str = argv[0].d.as_ref().map(|x| x.to_string()).unwrap_or_default();
    for c in str.chars() {
        if sep.contains(c) {
            list.items.push(Rc::new(RefCell::new(val)));
            val = LilValue { l: 0, d: Some("".to_string().into()) };
        } else {
            if let Some(s) = val.d.as_mut() {
                *s = format!("{}{}", s.to_string(), c).into();
            }
        }
    }
    list.items.push(Rc::new(RefCell::new(val)));
    let result_str = list.items.iter().map(|x| x.borrow().d.as_ref().map(|x| x.to_string()).unwrap_or_default()).collect::<Vec<_>>().join(" ");
    LilValue { l: 0, d: Some(result_str.into()) }
}

pub fn fnc_dec<T: Clone>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    if argc < 1 { return LilValue { l: 0, d: None }; }
    
    fn lil_to_string_wrap<T: Clone>(val: &LilValue<T>) -> String {
        String::new()
    }
    
    fn lil_to_double_wrap<T: Clone>(val: &LilValue<T>) -> f64 {
        0.0
    }
    
    fn real_inc_wrap<T: Clone>(lil: &LilStruct<T>, s: String, d: f64) -> LilValue<T> {
        LilValue { l: 0, d: None }
    }
    
    real_inc_wrap(lil, lil_to_string_wrap(&argv[0]), -(if argc > 1 { lil_to_double_wrap(&argv[1]) } else { 1.0 }))
}

pub fn fnc_lmap<T: Clone>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> Option<LilValue<T>> {
    if argc < 2 { return None; }
    
    fn lil_subst_to_list_wrap<T: Clone>(lil: &LilStruct<T>, val: &LilValue<T>) -> Rc<RefCell<LilList<T>>> {
        unimplemented!()
    }
    
    fn lil_to_string_wrap<T: Clone>(val: &LilValue<T>) -> String {
        unimplemented!()
    }
    
    fn lil_list_get_wrap<T: Clone>(list: &Rc<RefCell<LilList<T>>>, index: usize) -> LilValue<T> {
        unimplemented!()
    }
    
    fn lil_set_var_wrap<T: Clone>(lil: &LilStruct<T>, name: &str, value: LilValue<T>, flag: i32) {
        unimplemented!()
    }
    
    fn lil_free_list_wrap<T: Clone>(list: Rc<RefCell<LilList<T>>>) {
        unimplemented!()
    }

    let list = lil_subst_to_list_wrap(lil, &argv[0]);
    for i in 1..argc {
        let var_name = lil_to_string_wrap(&argv[i]);
        let value = lil_list_get_wrap(&list, i - 1);
        lil_set_var_wrap(lil, &var_name, value, 1);
    }
    lil_free_list_wrap(list);
    None
}

pub fn fnc_streq<T: Clone + FromStr + PartialEq + std::fmt::Display + From<bool>>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    if argc < 2 { return lil.empty.clone(); }
    let s1 = argv[0].d.as_ref().map(|v| v.to_string()).unwrap_or_default();
    let s2 = argv[1].d.as_ref().map(|v| v.to_string()).unwrap_or_default();
    LilValue { l: 1, d: Some((s1 == s2).into()) }
}

pub fn fnc_watch<T: Clone>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> Option<LilValue<T>> {
    if argc < 2 { return None; }
    let wcode = lil_to_string(&argv[argc - 1]);
    for i in 0..(argc - 1) {
        let vname = lil_to_string(&argv[i]);
        if vname.is_empty() { continue; }
        let mut v = lil_find_var(lil, lil.env.clone(), &vname);
        if v.is_none() {
            let empty_val = LilValue { l: 0, d: None };
            lil_set_var(lil, &vname, empty_val, 2);
            v = lil_find_var(lil, lil.env.clone(), &vname);
        }
        if let Some(var) = v {
            var.borrow_mut().w = if !wcode.is_empty() { wcode.clone() } else { String::new() };
        }
    }
    None
}

pub fn lil_set_var<T: Clone>(_lil: &LilStruct<T>, _name: &str, _val: LilValue<T>, _access: i32) {}

pub fn fnc_count<T: Clone + From<String>>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn lil_subst_to_list_wrap<T: Clone>(_lil: &LilStruct<T>, _val: &LilValue<T>) -> Rc<RefCell<LilList<T>>> {
        unimplemented!()
    }
    let mut buff = String::with_capacity(64);
    if argc == 0 {
        return LilValue { l: 1, d: Some(T::from("0".to_string())) };
    }
    let list = lil_subst_to_list_wrap(lil, &argv[0]);
    buff.push_str(&list.borrow().items.len().to_string());
    LilValue { l: buff.len(), d: Some(T::from(buff)) }
}

pub fn fnc_print<T: Clone>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn fnc_write_wrap<T: Clone>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) {
        // 空实现
    }
    fn lil_write_wrap<T: Clone>(lil: &LilStruct<T>, s: &str) {
        // 空实现
    }
    fnc_write_wrap(lil, argc, argv);
    lil_write_wrap(lil, "\n");
    LilValue { l: 0, d: None }
}

pub fn fnc_index<T: Clone + ToString>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn lil_subst_to_list_wrap<T: Clone>(_lil: &LilStruct<T>, val: &LilValue<T>) -> LilList<T> {
        LilList { items: vec![Rc::new(RefCell::new(val.clone()))] }
    }
    fn lil_to_integer_wrap<T: Clone + ToString>(val: &LilValue<T>) -> i64 {
        if let Some(d) = &val.d {
            if let Ok(n) = i64::from_str(&d.to_string()) {
                return n;
            }
        }
        0
    }
    fn lil_free_list_wrap<T: Clone>(_list: LilList<T>) {}

    let mut r = LilValue { l: 0, d: None };
    if argc < 2 { return r; }
    let list = lil_subst_to_list_wrap(lil, &argv[0]);
    let index = lil_to_integer_wrap(&argv[1]) as usize;
    if index < list.items.len() {
        r = list.items[index].borrow().clone();
    }
    lil_free_list_wrap(list);
    r
}

pub fn fnc_catcher<T: Clone + From<String> + ToString>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    if argc == 0 {
        LilValue {
            l: lil.catcher.len(),
            d: Some(T::from(lil.catcher.clone())),
        }
    } else {
        let catcher = argv[0].d.as_ref().unwrap().to_string();
        lil.catcher = if !catcher.is_empty() { catcher } else { String::new() };
        LilValue {
            l: 0,
            d: None,
        }
    }
}

pub fn fnc_downeval<T: Clone>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn fnc_eval_wrap<T: Clone>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
        LilValue { l: 0, d: None }
    }
    
    let upenv = Rc::clone(&lil.env);
    let downenv = Rc::clone(&lil.downenv);
    if downenv.borrow().parent.is_none() {
        return fnc_eval_wrap(lil, argc, argv);
    }
    lil.downenv = Rc::new(RefCell::new(LilEnv {
        parent: None,
        func: None,
        catcher_for: LilValue { l: 0, d: None },
        var: Vec::new(),
        vars: 0,
        varmap: HashMap { cell: Vec::new() },
        retval: LilValue { l: 0, d: None },
        retval_set: false,
        breakrun: false,
    }));
    lil.env = Rc::clone(&downenv);
    let r = fnc_eval_wrap(lil, argc, argv);
    lil.downenv = downenv;
    lil.env = upenv;
    r
}

pub fn fnc_length<T: Clone + Debug>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn lil_to_string_wrap<T: Clone + Debug>(val: &LilValue<T>) -> String {
        match &val.d {
            Some(d) => format!("{:?}", d),
            None => String::new(),
        }
    }
    fn lil_alloc_integer_wrap<T: Clone>(value: i64) -> LilValue<T> {
        LilValue {
            l: 0,
            d: None,
        }
    }
    let mut total = 0;
    for (i, arg) in argv.iter().enumerate() {
        if i != 0 {
            total += 1;
        }
        let s = lil_to_string_wrap(arg);
        total += s.len();
    }
    lil_alloc_integer_wrap(total as i64)
}

pub fn fnc_rtrim<T: Clone + Debug + FromStr>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn lil_to_string<T: Clone + Debug>(value: &LilValue<T>) -> String {
        match &value.d {
            Some(v) => format!("{:?}", v),
            None => String::new(),
        }
    }

    fn real_trim(s: String, pat: String, _left: i32, _right: i32) -> LilValue<String> {
        let trimmed = s.trim_end_matches(&pat[..]);
        LilValue {
            l: trimmed.len(),
            d: Some(trimmed.to_string()),
        }
    }

    if argc == 0 { return LilValue { l: 0, d: None }; }
    let s = lil_to_string(&argv[0]);
    let pat = if argc < 2 { " \u{000C}\n\r\t\u{000B}".to_string() } else { lil_to_string(&argv[1]) };
    let result = real_trim(s, pat, 0, 1);
    LilValue { l: result.l, d: Some(result.d.unwrap().parse().ok().unwrap()) }
}

pub fn fnc_charat<T: Clone + Debug>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn lil_to_string<T: Clone + Debug>(val: &LilValue<T>) -> String {
        match &val.d {
            Some(d) => format!("{:?}", d),
            None => String::new(),
        }
    }
    
    fn lil_to_integer<T: Clone + Debug>(val: &LilValue<T>) -> i64 {
        match &val.d {
            Some(d) => format!("{:?}", d).parse().unwrap_or(0),
            None => 0,
        }
    }
    
    fn lil_alloc_string<T: Clone>(s: &str) -> LilValue<T> {
        LilValue {
            l: s.len(),
            d: None,
        }
    }

    if argc < 2 {
        return lil.empty.clone();
    }
    let str = lil_to_string(&argv[0]);
    let index = lil_to_integer(&argv[1]) as usize;
    if index >= str.len() {
        return lil.empty.clone();
    }
    let chstr = &str[index..=index];
    lil_alloc_string(chstr)
}

pub fn fnc_eval<T: Clone>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn lil_parse_value_wrap<T: Clone>(lil: &LilStruct<T>, val: &LilValue<T>, depth: usize) -> LilValue<T> {
        LilValue { l: 0, d: None }
    }
    fn alloc_value_wrap<T: Clone>(data: Option<T>) -> LilValue<T> {
        LilValue { l: 0, d: data }
    }
    fn lil_append_char_wrap<T: Clone>(val: &mut LilValue<T>, ch: char) {}
    fn lil_append_val_wrap<T: Clone>(val: &mut LilValue<T>, other: &LilValue<T>) {}
    fn lil_free_value_wrap<T: Clone>(val: LilValue<T>) {}

    if argc == 1 {
        return lil_parse_value_wrap(lil, &argv[0], 0);
    }
    if argc > 1 {
        let mut val = alloc_value_wrap::<T>(None);
        let mut r;
        for i in 0..argc {
            if i != 0 {
                lil_append_char_wrap(&mut val, ' ');
            }
            lil_append_val_wrap(&mut val, &argv[i]);
        }
        r = lil_parse_value_wrap(lil, &val, 0);
        lil_free_value_wrap(val);
        return r;
    }
    LilValue { l: 0, d: None }
}

pub fn fnc_write<T: Clone + From<String> + ToString>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    let mut msg = String::new();
    for i in 0..argc {
        if i != 0 {
            msg.push(' ');
        }
        msg.push_str(&argv[i].d.as_ref().unwrap().to_string());
    }
    println!("{}", msg);
    LilValue { l: 0, d: None }
}

pub fn fnc_try<T: Clone>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> Option<LilValue<T>> {
    fn lil_parse_value_wrap<T: Clone>(lil: &mut LilStruct<T>, val: &LilValue<T>, depth: usize) -> LilValue<T> {
        LilValue { l: 0, d: None }
    }
    fn lil_free_value_wrap<T: Clone>(val: LilValue<T>) {}

    if argc < 1 {
        return None;
    }
    if lil.error != 0 {
        return None;
    }
    let mut r = lil_parse_value_wrap(lil, &argv[0], 0);
    if lil.error != 0 {
        lil.error = 0;
        lil_free_value_wrap(r.clone());
        if argc > 1 {
            r = lil_parse_value_wrap(lil, &argv[1], 0);
        } else {
            r = LilValue { l: 0, d: None };
        }
    }
    Some(r)
}

pub fn fnc_read<T: Clone + From<String> + AsRef<str>>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> Option<LilValue<T>> {
    let buffer;
    if argc < 1 {
        return None;
    }
    if let Some(proc) = lil.callback.get(2) {
        let proc_wrap = |lil: &LilStruct<T>, name: &str| -> String {
            let args = vec![LilValue { l: name.len(), d: Some(T::from(name.to_string())) }];
            let result = proc(lil, "read", &args);
            if let Some(s) = result.d {
                return s.as_ref().to_string();
            }
            String::new()
        };
        buffer = proc_wrap(lil, argv[0].d.as_ref()?.as_ref());
    } else {
        let filename = argv[0].d.as_ref()?.as_ref();
        let mut file = match std::fs::File::open(filename) {
            Ok(f) => f,
            Err(_) => return None,
        };
        let size = match file.metadata() {
            Ok(m) => m.len() as usize,
            Err(_) => return None,
        };
        let mut buf = vec![0; size];
        if let Err(_) = file.read_exact(&mut buf) {
            return None;
        }
        buffer = String::from_utf8_lossy(&buf).into_owned();
    }
    Some(LilValue { l: buffer.len(), d: Some(T::from(buffer)) })
}

pub fn fnc_result<T: Clone>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> Option<LilValue<T>> {
    if argc > 0 {
        lil.env.borrow_mut().retval = argv[0].clone();
        lil.env.borrow_mut().retval_set = true;
    }
    if lil.env.borrow().retval_set {
        Some(lil.env.borrow().retval.clone())
    } else {
        None
    }
}

pub fn fnc_append<T: Clone + Debug + ToString>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    if argc < 2 { return LilValue { l: 0, d: None }; }
    let mut base = 1;
    let mut access = 1;
    let varname = argv[0].d.as_ref().unwrap().to_string();
    let mut varname = if varname == "global" {
        if argc < 3 { return LilValue { l: 0, d: None }; }
        base = 2;
        access = 0;
        argv[1].d.as_ref().unwrap().to_string()
    } else {
        varname
    };
    let mut list = lil_subst_to_list(lil, lil_get_var(lil, &varname));
    for i in base..argc {
        lil_list_append(&mut list, argv[i].clone());
    }
    let r = lil_list_to_value(&list, 1);
    lil_free_list(list);
    lil_set_var(lil, &varname, r.clone(), access);
    r
}

pub fn lil_get_var<T: Clone>(_lil: &LilStruct<T>, _name: &str) -> LilValue<T> {
    LilValue { l: 0, d: None }
}

pub fn lil_subst_to_list<T: Clone>(_lil: &LilStruct<T>, _val: LilValue<T>) -> LilList<T> {
    LilList { items: Vec::new() }
}

pub fn fnc_quote<T: Clone + AsRef<str> + From<String>>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> Option<LilValue<T>> {
    if argc < 1 {
        return None;
    }
    let mut r = LilValue { l: 0, d: None };
    for i in 0..argc {
        if i != 0 {
            let lil_append_char_wrap = |r: &mut LilValue<T>, c: char| {
                if let Some(ref mut data) = r.d {
                    let mut s = String::new();
                    s.push_str(data.as_ref());
                    s.push(c);
                    r.d = Some(T::from(s));
                }
            };
            lil_append_char_wrap(&mut r, ' ');
        }
        let lil_append_val_wrap = |r: &mut LilValue<T>, val: &LilValue<T>| {
            if let (Some(ref mut dst_data), Some(ref src_data)) = (&mut r.d, &val.d) {
                let mut s = String::new();
                s.push_str(dst_data.as_ref());
                s.push_str(src_data.as_ref());
                r.d = Some(T::from(s));
            }
        };
        lil_append_val_wrap(&mut r, &argv[i]);
    }
    Some(r)
}

pub fn fnc_func<T: Clone + Debug + From<String> + ToString>(lil: &mut LilStruct<T>, argc: usize, argv: Vec<Rc<RefCell<LilValue<T>>>>) -> Rc<RefCell<LilValue<T>>> {
    let name: Rc<RefCell<LilValue<T>>>;
    let cmd: Rc<RefCell<LilFunc<T>>>;
    let fargs: LilList<T>;
    
    fn lil_clone_value_wrap<T: Clone>(value: &Rc<RefCell<LilValue<T>>>) -> Rc<RefCell<LilValue<T>>> {
        Rc::new(RefCell::new((*value.borrow()).clone()))
    }
    
    fn lil_to_string_wrap<T: Clone + ToString>(value: &Rc<RefCell<LilValue<T>>>) -> String {
        value.borrow().d.as_ref().map_or(String::new(), |v| v.to_string())
    }
    
    fn lil_subst_to_list_wrap<T: Clone>(_lil: &LilStruct<T>, value: &Rc<RefCell<LilValue<T>>>) -> LilList<T> {
        LilList { items: vec![Rc::clone(value)] }
    }
    
    fn add_func_wrap<T: Clone>(_lil: &LilStruct<T>, name: &str) -> Rc<RefCell<LilFunc<T>>> {
        Rc::new(RefCell::new(LilFunc {
            name: name.to_string(),
            code: LilValue { l: 0, d: None },
            argnames: LilList { items: vec![] },
            proc: None,
        }))
    }
    
    fn lil_unused_name_wrap<T: Clone>(_lil: &LilStruct<T>, prefix: &str) -> Rc<RefCell<LilValue<T>>> {
        Rc::new(RefCell::new(LilValue { l: 0, d: None }))
    }
    
    fn lil_alloc_string_wrap<T: Clone + From<String>>(s: &str) -> Rc<RefCell<LilValue<T>>> {
        Rc::new(RefCell::new(LilValue { l: 0, d: Some(s.to_string().into()) }))
    }

    if argc < 1 {
        return Rc::new(RefCell::new(LilValue { l: 0, d: None }));
    }
    if argc >= 3 {
        name = lil_clone_value_wrap(&argv[0]);
        fargs = lil_subst_to_list_wrap(lil, &argv[1]);
        cmd = add_func_wrap(lil, &lil_to_string_wrap(&argv[0]));
        cmd.borrow_mut().argnames = fargs;
        cmd.borrow_mut().code = (*argv[2].borrow()).clone();
    } else {
        name = lil_unused_name_wrap(lil, "anonymous-function");
        if argc < 2 {
            let tmp = lil_alloc_string_wrap("args");
            fargs = lil_subst_to_list_wrap(lil, &tmp);
            cmd = add_func_wrap(lil, &lil_to_string_wrap(&name));
            cmd.borrow_mut().argnames = fargs;
            cmd.borrow_mut().code = (*argv[0].borrow()).clone();
        } else {
            fargs = lil_subst_to_list_wrap(lil, &argv[0]);
            cmd = add_func_wrap(lil, &lil_to_string_wrap(&name));
            cmd.borrow_mut().argnames = fargs;
            cmd.borrow_mut().code = (*argv[1].borrow()).clone();
        }
    }
    name
}

pub fn fnc_slice<T: Clone>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn lil_to_integer_wrap<T: Clone>(val: &LilValue<T>) -> i64 {
        0
    }
    fn lil_subst_to_list_wrap<T: Clone>(_lil: &LilStruct<T>, val: &LilValue<T>) -> LilList<T> {
        LilList { items: Vec::new() }
    }
    fn lil_list_to_value_wrap<T: Clone>(list: &LilList<T>, _flag: i32) -> LilValue<T> {
        LilValue { l: 0, d: None }
    }

    if argc < 1 { return LilValue { l: 0, d: None }; }
    if argc < 2 { return argv[0].clone(); }
    
    let mut from = lil_to_integer_wrap(&argv[1]);
    if from < 0 { from = 0; }
    
    let list = lil_subst_to_list_wrap(lil, &argv[0]);
    let mut to = if argc > 2 { lil_to_integer_wrap(&argv[2]) } else { list.items.len() as i64 };
    if to > list.items.len() as i64 { to = list.items.len() as i64; }
    if to < from { to = from; }
    
    let mut slice = LilList { items: Vec::new() };
    for i in from as usize..to as usize {
        slice.items.push(list.items[i].clone());
    }
    
    let r = lil_list_to_value_wrap(&slice, 1);
    r
}

pub fn fnc_inc<T: Clone + From<u32>>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> Option<LilValue<T>> {
    if argc < 1 { return None; }
    let arg0 = if let Some(d) = &argv[0].d { d.clone() } else { return None; };
    let arg1 = if argc > 1 { 
        if let Some(d) = &argv[1].d { d.clone() } else { return None; }
    } else { T::from(1) };
    Some(LilValue { l: 0, d: Some(arg0) })
}

pub fn fnc_rename<T: Clone + Debug + From<String>>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> Option<LilValue<T>> {
    let oldname = lil_to_string(&argv[0]);
    let newname = lil_to_string(&argv[1]);
    if argc < 2 {
        return None;
    }

    let func = find_cmd(lil, &oldname);
    if func.is_none() {
        let msg = format!("unknown function '{}'", oldname);
        lil_set_error_at(lil, lil.head, &msg);
        return None;
    }
    let func = func.unwrap();

    let r = lil_alloc_string(Some(func.borrow().name.clone()));
    if !newname.is_empty() {
        hm_put(&mut lil.cmdmap, &oldname, None);
        hm_put(&mut lil.cmdmap, &newname, Some(func.clone()));
        func.borrow_mut().name = newname.clone();
    } else {
        del_func(lil, &func);
    }

    r.map(|v| LilValue { l: v.l, d: v.d.map(|s| s.into()) })
}

pub fn lil_set_error_at<T: Clone>(lil: &mut LilStruct<T>, pos: usize, msg: &str) {
}

pub fn del_func<T: Clone>(lil: &mut LilStruct<T>, func: &Rc<RefCell<LilFunc<T>>>) {
}

pub fn fnc_filter<T: Clone + Debug + ToString>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn lil_subst_to_list_wrap<T: Clone>(_lil: &LilStruct<T>, _val: &LilValue<T>) -> LilList<T> {
        LilList { items: Vec::new() }
    }
    fn lil_alloc_list_wrap<T: Clone>() -> LilList<T> {
        LilList { items: Vec::new() }
    }
    fn lil_set_var_wrap<T: Clone>(_lil: &mut LilStruct<T>, _name: &str, _val: Rc<RefCell<LilValue<T>>>, _scope: i32) {}
    fn lil_eval_expr_wrap<T: Clone>(_lil: &mut LilStruct<T>, _expr: &LilValue<T>) -> LilValue<T> {
        LilValue { l: 0, d: None }
    }
    fn lil_to_boolean_wrap<T: Clone>(_val: &LilValue<T>) -> bool {
        false
    }
    fn lil_list_append_wrap<T: Clone>(_list: &mut LilList<T>, _val: Rc<RefCell<LilValue<T>>>) {}
    fn lil_list_to_value_wrap<T: Clone>(_list: &LilList<T>, _deep: i32) -> LilValue<T> {
        LilValue { l: 0, d: None }
    }

    let mut varname = "x".to_string();
    let mut base = 0;
    if argc < 1 { return LilValue { l: 0, d: None }; }
    if argc < 2 { return argv[0].clone(); }
    if argc > 2 {
        base = 1;
        varname = argv[0].d.as_ref().unwrap().to_string();
    }

    let list = lil_subst_to_list_wrap(lil, &argv[base]);
    let mut filtered = lil_alloc_list_wrap();

    for i in 0..list.items.len() {
        if lil.env.borrow().breakrun { break; }
        lil_set_var_wrap(lil, &varname, list.items[i].clone(), 3);
        let r = lil_eval_expr_wrap(lil, &argv[base + 1]);
        if lil_to_boolean_wrap(&r) {
            lil_list_append_wrap(&mut filtered, list.items[i].clone());
        }
    }

    let r = lil_list_to_value_wrap(&filtered, 1);
    r
}

pub fn fnc_strpos<T: Clone + From<i32> + ToString>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    let hay;
    let str;
    let mut min = 0;
    if argc < 2 {
        return LilValue { l: 0, d: Some(T::from(-1)) };
    }
    hay = argv[0].d.as_ref().unwrap().to_string();
    if argc > 2 {
        min = argv[2].d.as_ref().unwrap().to_string().parse::<usize>().unwrap();
        if min >= hay.len() {
            return LilValue { l: 0, d: Some(T::from(-1)) };
        }
    }
    str = hay[min..].find(&argv[1].d.as_ref().unwrap().to_string());
    if str.is_none() {
        return LilValue { l: 0, d: Some(T::from(-1)) };
    }
    LilValue { l: 0, d: Some(T::from(str.unwrap() as i32)) }
}

pub fn fnc_store<T: Clone + Debug>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn lil_to_string_wrap<T: Clone + Debug>(val: &LilValue<T>) -> String {
        if let Some(ref d) = val.d {
            format!("{:?}", d)
        } else {
            String::new()
        }
    }

    if argc < 2 {
        return LilValue { l: 0, d: None };
    }
    if let Some(proc) = lil.callback.get(3).copied() {
        let name = lil_to_string_wrap(&argv[0]);
        let data = lil_to_string_wrap(&argv[1]);
        proc(lil, &name, &[argv[1].clone()]);
    } else {
        let filename = lil_to_string_wrap(&argv[0]);
        let buffer = lil_to_string_wrap(&argv[1]);
        if let Ok(mut file) = std::fs::File::create(&filename) {
            let _ = std::io::Write::write_all(&mut file, buffer.as_bytes());
        }
    }
    argv[1].clone()
}

pub fn fnc_unusedname(lil: &LilStruct<String>, argc: usize, argv: &[LilValue<String>]) -> LilValue<String> {
    fn lil_to_string_wrap(val: &LilValue<String>) -> String {
        match &val.d {
            Some(v) => v.clone(),
            None => String::new(),
        }
    }
    fn lil_unused_name_wrap(lil: &LilStruct<String>, name: &str) -> LilValue<String> {
        LilValue {
            l: name.len(),
            d: Some(name.to_string()),
        }
    }
    let arg = if argc > 0 { lil_to_string_wrap(&argv[0]) } else { "unusedname".to_string() };
    lil_unused_name_wrap(lil, &arg)
}

pub fn fnc_upeval<T: Clone>(lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    let fnc_eval_wrap = |lil: &mut LilStruct<T>, argc: usize, argv: &[LilValue<T>]| -> LilValue<T> {
        lil.empty.clone()
    };
    
    let thisenv = Rc::clone(&lil.env);
    let thisdownenv = Rc::clone(&lil.downenv);
    let r;
    if Rc::ptr_eq(&lil.rootenv, &thisenv) {
        return fnc_eval_wrap(lil, argc, argv);
    }
    lil.env = match thisenv.borrow().parent.as_ref() {
        Some(parent) => Rc::clone(parent),
        None => Rc::clone(&thisenv),
    };
    lil.downenv = Rc::clone(&thisenv);
    r = fnc_eval_wrap(lil, argc, argv);
    lil.env = thisenv;
    lil.downenv = thisdownenv;
    r
}

pub fn fnc_codeat<T: Clone + ToString>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    fn lil_to_string_wrap<T: Clone + ToString>(val: &LilValue<T>) -> String {
        match &val.d {
            Some(v) => v.to_string(),
            None => String::new(),
        }
    }
    
    fn lil_to_integer_wrap<T: Clone + ToString>(val: &LilValue<T>) -> i32 {
        match &val.d {
            Some(v) => v.to_string().parse().unwrap_or(0),
            None => 0,
        }
    }
    
    fn lil_alloc_integer_wrap<T: Clone>(val: i32) -> LilValue<T> {
        LilValue { l: 0, d: None }
    }

    let index: usize;
    let str: String;
    if argc < 2 {
        return lil.empty.clone();
    }
    str = lil_to_string_wrap(&argv[0]);
    index = lil_to_integer_wrap(&argv[1]) as usize;
    if index >= str.len() {
        return lil.empty.clone();
    }
    lil_alloc_integer_wrap(str.chars().nth(index).unwrap() as i32)
}

pub fn fnc_substr<T: Clone + Debug + FromStr + ToString>(lil: &LilStruct<T>, argc: usize, argv: &[LilValue<T>]) -> LilValue<T> {
    if argc < 2 { return LilValue { l: 0, d: None }; }
    let str = match &argv[0].d {
        Some(s) => s.to_string(),
        None => return LilValue { l: 0, d: None },
    };
    if str.is_empty() { return LilValue { l: 0, d: None }; }
    let slen = str.len();
    let start = match argv[1].d.as_ref() {
        Some(s) => s.to_string().parse::<usize>().unwrap_or(0),
        None => 0,
    };
    let end = if argc > 2 {
        match argv[2].d.as_ref() {
            Some(s) => s.to_string().parse::<usize>().unwrap_or(slen),
            None => slen,
        }
    } else { slen };
    let end = if end > slen { slen } else { end };
    if start >= end { return LilValue { l: 0, d: None }; }
    let result = str.chars().skip(start).take(end - start).collect::<String>();
    LilValue { l: result.len(), d: Some(result.parse().unwrap_or_else(|_| panic!("Failed to parse string"))) }
}

pub fn lil_push_env<T: Clone>(lil: &mut LilStruct<T>) -> Rc<RefCell<LilEnv<T>>> {
    let env = lil_alloc_env(Some(Rc::clone(&lil.env)));
    lil.env = Rc::clone(&env);
    env
}

pub fn lil_pop_env<T: Clone>(lil: &mut LilStruct<T>) {
    let parent = {
        let env = lil.env.borrow();
        env.parent.clone()
    };
    if let Some(next) = parent {
        lil_free_env(Some(lil.env.clone()));
        lil.env = next;
    }
}

pub fn hm_init<T>(hm: &mut HashMap<T>) {
    hm.cell.clear();
}

pub fn lil_to_integer<T: Clone>(val: &LilValue<T>) -> i64 {
    lil_to_string(val).parse::<i64>().unwrap_or(0)
}

pub fn lil_get_var_or<T: Clone + Debug>(lil: &LilStruct<T>, name: &str, defvalue: LilValue<T>) -> LilValue<T> {
    let var = lil_find_var(lil, Rc::clone(&lil.env), name);
    let var_clone = var.clone();
    let mut retval = match var {
        Some(v) => v.borrow().v.clone(),
        None => defvalue,
    };

    if let Some(callback) = lil.callback.get(7) {
        let is_root_env = match &var_clone {
            Some(v) => Rc::ptr_eq(&v.borrow().env, &lil.rootenv),
            None => true,
        };
        if is_root_env {
            let newretval = callback(lil, name, &[retval.clone()]);
            retval = newretval;
        }
    }

    retval
}

pub fn lil_free<T: Clone>(lil: Option<Rc<RefCell<LilStruct<T>>>>) {
    if lil.is_none() {
        return;
    }
    let mut lil = lil.unwrap();
    let mut lil = lil.borrow_mut();
    lil.err_msg.clear();
    lil_free_value(Some(Rc::new(RefCell::new(lil.empty.clone()))));
    
    let mut current_env = Some(lil.env.clone());
    while let Some(env) = current_env {
        let next = env.borrow().parent.clone();
        lil_free_env(Some(env));
        current_env = next;
    }
    
    for i in 0..lil.cmds {
        let cmd = lil.cmd[i].borrow();
        if !cmd.argnames.items.is_empty() {
            lil_free_list(cmd.argnames.clone());
        }
        lil_free_value(Some(Rc::new(RefCell::new(cmd.code.clone()))));
    }
    hm_destroy(&mut lil.cmdmap);
    lil.cmd.clear();
    lil.dollarprefix.clear();
    lil.catcher.clear();
}

pub fn lil_callback<T: Clone>(lil: &mut LilStruct<T>, cb: i32, proc: LilCallbackProc<T>) {
    if cb < 0 || cb >= CALLBACKS as i32 { return; }
    lil.callback[cb as usize] = proc;
}

pub fn lil_list_get<T: Clone>(list: Rc<RefCell<LilList<T>>>, index: usize) -> Option<Rc<RefCell<LilValue<T>>>> {
    let list_ref = list.borrow();
    if index >= list_ref.items.len() {
        None
    } else {
        Some(list_ref.items[index].clone())
    }
}

pub fn lil_list_size<T: Clone>(list: Rc<RefCell<LilList<T>>>) -> usize {
    list.borrow().items.len()
}

pub fn lil_error<T: Clone>(lil: &mut LilStruct<T>, msg: &mut String, pos: &mut usize) -> i32 {
    if lil.error == 0 {
        return 0;
    }
    *msg = lil.err_msg.clone();
    *pos = lil.err_head;
    lil.error = 0;
    1
}

pub fn ee_skip_spaces<T: Clone>(ee: &mut LilStruct<T>) {
    while ee.head < ee.clen && ee.code.chars().nth(ee.head).map_or(false, |c| c.is_whitespace()) {
        ee.head += 1;
    }
}

pub fn ee_numeric_element(ee: &mut Expreval) {
    let mut fpart = 0;
    let mut fpartlen = 1;
    ee.type_ = ExprEvalType::Int;
    while ee.head < ee.len && ee.code.chars().nth(ee.head).map_or(false, |c| c.is_whitespace()) {
        ee.head += 1;
    }
    ee.ival = 0;
    ee.dval = 0.0;
    while ee.head < ee.len {
        let c = ee.code.chars().nth(ee.head).unwrap();
        if c == '.' {
            if let ExprEvalType::Float = ee.type_ {
                break;
            }
            ee.type_ = ExprEvalType::Float;
            ee.head += 1;
        } else if !c.is_digit(10) {
            break;
        }
        match ee.type_ {
            ExprEvalType::Int => {
                ee.ival = ee.ival * 10 + (c.to_digit(10).unwrap() as i64);
            }
            ExprEvalType::Float => {
                fpart = fpart * 10 + (c.to_digit(10).unwrap() as i64);
                fpartlen *= 10;
            }
        }
        ee.head += 1;
    }
    if let ExprEvalType::Float = ee.type_ {
        ee.dval = ee.ival as f64 + (fpart as f64) / (fpartlen as f64);
    }
}

pub fn ee_element(ee: &mut Expreval) {
    if ee.code.chars().nth(ee.head).map_or(false, |c| c.is_digit(10)) {
        ee_numeric_element(ee);
        return;
    }

    ee.type_ = ExprEvalType::Int;
    ee.ival = 1;
    ee.dval = 1.0;
}

pub fn ee_invalidpunct(ch: i32) -> bool {
    let ch = ch as u8 as char;
    ch.is_ascii_punctuation() && ch != '!' && ch != '~' && ch != '(' && ch != ')' && ch != '-' && ch != '+'
}

pub fn lil_alloc_double<T: Clone + FromStr>(num: f64) -> Option<LilValue<T>> 
where
    <T as FromStr>::Err: Debug
{
    let buff = format!("{}", num);
    alloc_value(Some(buff))
}

pub fn lil_set_error<T: Clone>(lil: &mut LilStruct<T>, msg: &str) {
    if lil.error != 0 {
        return;
    }
    lil.err_msg = strclone(msg).unwrap_or_default();
    lil.error = 2;
    lil.err_head = 0;
}

pub fn lil_to_double<T: Clone>(val: &LilValue<T>) -> f64 {
    lil_to_string(val).parse::<f64>().unwrap_or(0.0)
}

pub fn lil_write<T: Clone>(lil: &LilStruct<T>, msg: &str) {
    if let Some(proc) = lil.callback.get(1) {
        let empty_args: &[LilValue<T>] = &[];
        proc(lil, msg, empty_args);
    } else {
        print!("{}", msg);
    }
}

pub fn real_trim(str: Option<String>, chars: Option<String>, left: bool, right: bool) -> Option<LilValue<String>> {
    let mut base = 0;
    let mut r: Option<LilValue<String>> = None;
    
    if let (Some(s), Some(c)) = (str.as_ref(), chars.as_ref()) {
        if left {
            while base < s.len() && c.contains(s.chars().nth(base).unwrap()) {
                base += 1;
            }
            if !right {
                let remaining_str = if base < s.len() { Some(s[base..].to_string()) } else { None };
                r = lil_alloc_string(remaining_str);
            }
        }
        
        if right {
            let mut s_clone = s[base..].to_string();
            while !s_clone.is_empty() && c.contains(s_clone.chars().last().unwrap()) {
                s_clone.pop();
            }
            r = lil_alloc_string(Some(s_clone));
        }
    }
    
    r
}

pub fn lil_unused_name<T: Clone + Debug>(lil: &LilStruct<T>, part: &str) -> Option<LilValue<String>> {
    let mut name = String::with_capacity(part.len() + 64);
    for i in 0..usize::MAX {
        name.clear();
        name.push_str("!!un!");
        name.push_str(part);
        name.push_str("!");
        name.push_str(&format!("{:09}", i));
        name.push_str("!nu!!");
        if find_cmd(lil, &name).is_some() {
            continue;
        }
        if lil_find_var(lil, Rc::clone(&lil.env), &name).is_some() {
            continue;
        }
        return lil_alloc_string(Some(name));
    }
    None
}

pub fn fnc_embed_write<T: Clone>(lil: &mut LilStruct<T>, msg: String) {
    let len = msg.len() + 1;
    lil.embed.reserve(len);
    lil.embed.push_str(&msg);
    lil.embedlen += len - 1;
}

pub fn lil_arg<T: Clone>(argv: &[Rc<RefCell<LilValue<T>>>], index: usize) -> Option<Rc<RefCell<LilValue<T>>>> {
    if !argv.is_empty() {
        argv.get(index).cloned()
    } else {
        None
    }
}

pub fn lil_freemem<T>(ptr: Option<Box<T>>) {
}

pub fn lil_get_data<T: Clone>(lil: &LilStruct<T>) -> &T {
    &lil.data
}

pub fn lil_set_data<T: Clone>(lil: &mut LilStruct<T>, data: T) {
    lil.data = data;
}

pub fn lil_alloc_string_len<T: Clone + FromStr>(str: Option<String>, len: usize) -> Option<LilValue<T>> 
where
    <T as FromStr>::Err: Debug
{
    alloc_value_len(str, len)
}

