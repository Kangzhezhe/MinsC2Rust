import os
import json
import re
import ast
from collections import defaultdict

class DataManager:
    def __init__(self, source_path,include_dict,all_pointer_funcs,include_dict_without_fn_pointer,has_test=True):
        self.has_test = has_test
        self.data = []
        self.path_index_dict = {}
        self.source_names = [os.path.splitext(os.path.basename(f))[0] for f in source_path]
        self.include_dict = include_dict
        self.include_dict_without_fn_pointer = include_dict_without_fn_pointer
        self.all_pointer_funcs = all_pointer_funcs
        self.comment = "// 注意：该函数不允许修改，因为工程中其他文件中的函数也调用了他们，如果修改了，会影响其他文件内函数的功能，只允许调用该函数\n"
        for f in source_path:
            with open(f, 'r') as file:
                self.data.append(json.load(file))

        # Build a fast function -> source index lookup for ownership resolution.
        self.func_to_indices = defaultdict(list)
        for idx, jsonfile in enumerate(self.data):
            for func_name in jsonfile.keys():
                if func_name != 'extra':
                    self.func_to_indices[func_name].append(idx)

        self.source_decl_details = {}
        self.decl_to_sources = defaultdict(list)
        self._decl_depends_cache = {}
        for idx, jsonfile in enumerate(self.data):
            source_name = self.source_names[idx]
            decl_details = self._extract_decl_details(jsonfile.get('extra', ''))
            self.source_decl_details[source_name] = decl_details
            for decl_name in decl_details.keys():
                if source_name not in self.decl_to_sources[decl_name]:
                    self.decl_to_sources[decl_name].append(source_name)

        self.decl_owner_map = {}
        for decl_name, candidate_sources in self.decl_to_sources.items():
            owner = self._resolve_decl_owner(decl_name, candidate_sources)
            if owner:
                self.decl_owner_map[decl_name] = owner

    @staticmethod
    def _extract_decl_details(source_extra):
        if not source_extra:
            return {}
        details_index = source_extra.find('extract_info')
        detail = source_extra[:details_index] if details_index != -1 else source_extra
        detail = detail.strip()
        if not detail:
            return {}
        try:
            converted = ast.literal_eval(detail)
        except (SyntaxError, ValueError):
            return {}
        if not isinstance(converted, dict):
            return {}
        return {
            key: value
            for key, value in converted.items()
            if isinstance(key, str) and key.isidentifier() and isinstance(value, str)
        }

    @staticmethod
    def _looks_like_test_source(source_name):
        tokens = [token for token in re.split(r'[^0-9A-Za-z_]+', source_name or '') if token]
        return any(token in {'test', 'tests'} or token.startswith('test_') for token in tokens)

    def _source_depends_on(self, source_name, target_name):
        if not source_name or not target_name or source_name == target_name:
            return False
        cache_key = (source_name, target_name)
        if cache_key in self._decl_depends_cache:
            return self._decl_depends_cache[cache_key]

        visited = set()
        stack = list(self.include_dict.get(source_name, []) or [])
        while stack:
            current = stack.pop()
            if current == target_name:
                self._decl_depends_cache[cache_key] = True
                return True
            if current in visited:
                continue
            visited.add(current)
            stack.extend(self.include_dict.get(current, []) or [])

        self._decl_depends_cache[cache_key] = False
        return False

    def _resolve_decl_owner(self, decl_name, candidate_sources):
        _ = decl_name
        unique_sources = []
        seen = set()
        for source_name in candidate_sources or []:
            if source_name in self.source_names and source_name not in seen:
                seen.add(source_name)
                unique_sources.append(source_name)

        if not unique_sources:
            return ''
        if len(unique_sources) == 1:
            return unique_sources[0]

        def rank(source_name):
            provided_to_others = sum(
                1
                for other in unique_sources
                if other != source_name and self._source_depends_on(other, source_name)
            )
            depends_on_others = sum(
                1
                for other in unique_sources
                if other != source_name and self._source_depends_on(source_name, other)
            )
            return (
                -provided_to_others,
                depends_on_others,
                1 if self._looks_like_test_source(source_name) else 0,
                self.source_names.index(source_name),
            )

        return sorted(unique_sources, key=rank)[0]

    def get_decl_owner(self, decl_name):
        return self.decl_owner_map.get(decl_name, '')

    def get_source_decl_names(self, source_name, owned_only=False):
        decl_names = set(self.source_decl_details.get(source_name, {}).keys())
        if not owned_only:
            return decl_names
        return {name for name in decl_names if self.decl_owner_map.get(name, '') == source_name}

    def get_owned_decl_details(self, source_name):
        return {
            name: detail
            for name, detail in self.source_decl_details.get(source_name, {}).items()
            if self.decl_owner_map.get(name, '') == source_name
        }
        
    def get_index_by_source_name(self,source_name):
        return self.source_names.index(source_name)

    def get_all_source(self,source_name,all_files,without_fn_pointer=False):
        if without_fn_pointer:
            child_source = self.include_dict_without_fn_pointer.get(source_name, [])
        else:
            child_source = self.include_dict.get(source_name, [])
        for source in child_source:
            if source not in all_files:
                all_files.append(source)
                self.get_all_source(source,all_files)
            
    def get_parent_sources(self, source_name, all_files):
        for parent, children in self.include_dict.items():
            if source_name in children and parent not in all_files:
                all_files.append(parent)
                self.get_parent_sources(parent, all_files)

    
    def get_include_indices(self,test_source_name,without_fn_pointer=False):
        all_include_files = [test_source_name]
        self.get_all_source(test_source_name,all_include_files,without_fn_pointer)
        include_files_indices = [self.source_names.index(file) for file in all_include_files if file in self.source_names]
        self.include_files_indices = include_files_indices
        self.all_include_files = all_include_files
        return include_files_indices,all_include_files

    
    def get_include_indices_with_parent(self, test_source_name):
        all_include_files = [test_source_name]
        self.get_all_source(test_source_name, all_include_files)
        for source in all_include_files.copy():
            self.get_parent_sources(source, all_include_files)
        for source in all_include_files.copy():
            self.get_all_source(source, all_include_files)
        include_files_indices = [self.source_names.index(file) for file in all_include_files if file in self.source_names]
        self.include_files_indices = include_files_indices
        self.all_include_files = all_include_files
        return include_files_indices, all_include_files

    def get_content(self, func_name, respect_scope=True, preferred_source=''):
        include_scope = set(range(len(self.data)))
        if respect_scope:
            include_scope = set(getattr(self, 'include_files_indices', range(len(self.data))))
        candidate_indices = [i for i in self.func_to_indices.get(func_name, []) if i in include_scope]
        if not candidate_indices:
            return "", "", -1

        if preferred_source and preferred_source in self.source_names:
            preferred_idx = self.source_names.index(preferred_source)
            if preferred_idx in candidate_indices:
                jsonfile = self.data[preferred_idx]
                return jsonfile[func_name], jsonfile["extra"], preferred_idx

        i = candidate_indices[0]
        jsonfile = self.data[i]
        return jsonfile[func_name], jsonfile["extra"], i

    def get_source_name_by_func_name(self, func_name, preferred_source='', respect_scope=True):
        include_scope = set(range(len(self.data)))
        if respect_scope:
            include_scope = set(getattr(self, 'include_files_indices', range(len(self.data))))
        candidate_indices = [i for i in self.func_to_indices.get(func_name, []) if i in include_scope]
        if not candidate_indices:
            return ''

        if preferred_source and preferred_source in self.source_names:
            preferred_idx = self.source_names.index(preferred_source)
            if preferred_idx in candidate_indices:
                return preferred_source

        return self.source_names[candidate_indices[0]]

    def get_result(self, func_name, results, respect_scope=True, preferred_source=''):
        owner = self.get_source_name_by_func_name(
            func_name,
            preferred_source=preferred_source,
            respect_scope=respect_scope,
        )
        if owner and func_name in results.get(owner, {}):
            return results[owner][func_name]

        include_scope = set(getattr(self, 'all_include_files', [])) if respect_scope else None
        for k, v in results.items() :
            if func_name in v and (include_scope is None or k in include_scope):
                return v[func_name]
        return ''

    def get_direct_child_functions(self, func_name, funcs_child):
        children = funcs_child.get(func_name, []) or []
        ordered = []
        seen = set()
        for child_fun in children:
            if child_fun not in seen:
                seen.add(child_fun)
                ordered.append(child_fun)
        return ordered

    def get_child_context(self, func_name, results, funcs_child, prompt_limit=float('inf'), respect_scope=True, direct_only=False, preferred_source=''):
        child_context = set()
        child_context_ret = ""
        extra_contents = []
        source_name = self.get_source_name_by_func_name(
            func_name,
            preferred_source=preferred_source,
            respect_scope=respect_scope,
        )
        extra_content = results.get(source_name, {}).get('extra', '') if source_name else ''
        if extra_content:
            extra_contents.append(extra_content)
        child_funs = ''
        if func_name in funcs_child:
            all_child_funs = (
                self.get_direct_child_functions(func_name, funcs_child)
                if direct_only
                else self.get_all_child_functions(func_name, funcs_child)
            )
            for child_fun in all_child_funs:
                child_func_content = self.get_result(
                    child_fun,
                    results,
                    respect_scope=respect_scope,
                    preferred_source=preferred_source,
                )
                if child_fun != func_name and child_func_content != '':
                    child_source_name = self.get_source_name_by_func_name(
                        child_fun,
                        preferred_source=preferred_source,
                        respect_scope=respect_scope,
                    )
                    extra = results.get(child_source_name, {}).get('extra', '') if child_source_name else ''
                    if extra and extra not in extra_contents:
                        extra_contents.append(extra)
                    if len(child_func_content) + len(child_context_ret) > prompt_limit:
                        child_context.add(child_func_content.lstrip().split('\n', 1)[0].replace('{', ';'))
                    else:
                        child_funs += child_fun + ","
                        child_context.add(child_func_content)
                    child_context_ret = '\n'.join(extra_contents + list(child_context))
        child_context_ret = '\n'.join(extra_contents + list(child_context))
        return child_context_ret, child_funs

    def get_child_context_c(self, func_name, results, funcs_child, respect_scope=True, direct_only=False, preferred_source=''):
        source_context, source_extra, i = self.get_content(
            func_name,
            respect_scope=respect_scope,
            preferred_source=preferred_source,
        )
        child_context = source_context
        child_funs = func_name + ","
        if func_name in funcs_child:
            all_child_funs = (
                self.get_direct_child_functions(func_name, funcs_child)
                if direct_only
                else self.get_all_child_functions(func_name, funcs_child)
            )
            for child_fun in all_child_funs:
                if child_fun != func_name and self.get_result(
                    child_fun,
                    results,
                    respect_scope=respect_scope,
                    preferred_source=preferred_source,
                ) == '':
                    child_funs += child_fun + ","
                    source_context, source_extra, _ = self.get_content(
                        child_fun,
                        respect_scope=respect_scope,
                        preferred_source=preferred_source,
                    )
                    child_context = child_context + '\n' + source_context
        return child_context, child_funs, ''

    def get_details(self, func_names,return_raw=False,respect_scope=True,preferred_source=''):
        before_details = ''
        seen_details = set()
        converted_dict = {}
        raw_details = set()
        for func_name in func_names:
            _, _, i = self.get_content(
                func_name,
                respect_scope=respect_scope,
                preferred_source=preferred_source,
            )
            if i == -1:
                continue
            jsonfile = self.data[i]
            source_extra = jsonfile['extra']
            detail_map = self._extract_decl_details(source_extra)
            if detail_map:
                detail_repr = repr(detail_map)
                if detail_repr not in seen_details:
                    seen_details.add(detail_repr)
                    converted_dict.update(detail_map)

            details_index = source_extra.find('extract_info')
            if details_index != -1:
                detail = source_extra[details_index:]
                if detail not in raw_details:
                    raw_details.add(detail)

        before_details = repr(converted_dict)
        # try:
        #     converted_dict = ast.literal_eval(before_details)
        # except (SyntaxError, ValueError):
        #     print("Error: Invalid string format for conversion.")
        #     converted_dict = {}

        if return_raw:
            return list(converted_dict.keys()), before_details, "\n".join(raw_details)
        else:
            return list(converted_dict.keys()), before_details

    def get_all_child_functions(self, func_name, funcs_child):
        all_child_funs = []
        queue = [func_name]  # 使用队列进行广度优先遍历

        while queue:
            current_func = queue.pop(0)  # 取出队列中的第一个节点
            if current_func in funcs_child:
                for child_fun in funcs_child[current_func]:
                    if child_fun not in all_child_funs:  # 避免重复添加
                        all_child_funs.append(child_fun)
                        queue.append(child_fun)  # 将子节点加入队列

        return all_child_funs

    def get_all_parent_functions(self,func_name, funcs_child):
        all_parent_funs = set()

        def add_parent_functions(func):
            for parent, children in funcs_child.items():
                if func in children and parent not in all_parent_funs:
                    all_parent_funs.add(parent)
                    add_parent_functions(parent)

        add_parent_functions(func_name)
        return all_parent_funs
