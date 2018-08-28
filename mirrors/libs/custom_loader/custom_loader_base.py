#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# code is far away from bugs with the god animal protect
# I love animals. They taste delicious.
#         ┌─┐       ┌─┐
#      ┌──┘ ┴───────┘ ┴──┐
#      │                 │
#      │       ───       │
#      │  ─┬┘       └┬─  │
#      │                 │
#      │       ─┴─       │
#      │                 │
#      └───┐         ┌───┘
#          │         │
#          │         │
#          │         │
#          │         └──────────────┐
#          │                        │
#          │      Gods Bless        ├─┐
#          │      Never Bugs        ┌─┘
#          │                        │
#          └─┐  ┐  ┌───────┬──┐  ┌──┘
#            │ ─┤ ─┤       │ ─┤ ─┤
#            └──┴──┘       └──┴──┘

import operator
from collections import OrderedDict
from mirrors.libs.utils import Singleton

from mirrors.common.options import FieldShowScene

ALL_REVERSE_FK_MODELS = "__ALL_REVERSE_FK_MODELS__"
DEFAULT_ORDER = 9999


class BaseModelManager(object):

    def __init__(self, model_name=None):
        from mirrors.models import get_model_by_name
        self.model_name = model_name
        self.model = get_model_by_name(model_name)
        self.never_show_keys = set()
        self.dependency_map = {}
        self.key_map_type = OrderedDict()
        self.has_type_keys = set()
        self.option_map = OrderedDict()
        self.registered_key = list()
        self.exclude_show_keys = set()
        self.reverse_fk_patch_info = OrderedDict()
        self.required_keys = set()
        self.show_scene = FieldShowScene.List
        self.control_able = {}
        self.scene = {}
        self.support_control_able = [
            'notexcelable',
            'notmasseditable',
            'datamultipleable',
            'multioperator',
            'memberable',
            'validaterules',
            'editable',
            'shareable',
            'orderable',
            'help_text',
            'disable_export',
            'ext_data',
            '__meta_model_name__',
            'notopenable',
        ]

    def cal_dependency(self, required_keys):
        v = set()
        ret = []

        def dfs(key):
            if key not in v:
                v.add(key)
                for dependee in self.dependency_map.get(key, []):
                    dfs(dependee)
                ret.append(key)

        for key in required_keys:
            dfs(key)

        return ret

    def add_dependency(self, dependent_iter, dependee_iter):
        # dependent depends on dependee
        def to_iter(arg):
            if isinstance(arg, list):
                return arg
            else:
                return [arg]

        for dependent in to_iter(dependent_iter):
            for dependee in to_iter(dependee_iter):
                self.dependency_map.setdefault(dependent, set())
                self.dependency_map[dependent].add(dependee)

    def _orderby_all_show_keys(self, ret, key=None):
        return self._orderby_scene_keys(ret, key)

    def _orderby_scene_keys(self, ret, key=None, scene_words=None):
        scene = self.scene
        if not scene:
            return ret

        if scene_words is None:
            scene_words = 'normal'

        if key is None:
            key = operator.itemgetter('name')

        show_keys = scene[scene_words]
        show_keys = self.set_show_keys(show_keys)

        new_ret = []
        for item in ret:
            order = show_keys.get(key(item))
            if order is not None:
                item['order'] = order
                new_ret.append({'item': item, 'order': order})
        new_ret.sort(key=operator.itemgetter('order'))
        return [_['item'] for _ in new_ret]

    def _process_add_kwargs(self, ret):
        for item in ret:
            name = item.get("name")
            control_able = self.control_able.get(name) or {}
            for k, v in control_able.iteritems():
                if k in self.support_control_able:
                    item.setdefault("type", {})
                    item["type"][k] = v
        return ret

    def _process_ret(self, ret):
        return ret

    def set_all_show_keys(self, keys):
        self.scene['normal'] = self.set_show_keys(keys)

    def scene_config(self, scene):
        self.scene = scene
        for k, v in self.scene.items():
            self.scene[k] = self.set_show_keys(v)

    def set_show_keys(self, keys):
        show_keys = OrderedDict()
        for idx, key in enumerate(keys):
            show_keys[key] = idx
        return show_keys

    def add_exclude_show_keys(self, keys):
        if hasattr(keys, '__iter__'):
            self.exclude_show_keys |= set(keys)
        else:
            self.exclude_show_keys |= {keys}

    def remove_exclude_show_keys(self, keys):
        if hasattr(keys, '__iter__'):
            self.exclude_show_keys -= set(keys)
        else:
            self.exclude_show_keys -= {keys}

    def set_exclude_show_keys(self, keys):
        if hasattr(keys, '__iter__'):
            self.exclude_show_keys = set(keys)
        else:
            self.exclude_show_keys = {keys}

    def add_always_required_keys(self, keys):
        if hasattr(keys, '__iter__'):
            self.always_required_keys = set(keys)
        else:
            self.always_required_keys = {keys}

    def add_all_show_keys(self, keys):
        for key in keys:
            self.add_to_all_show_keys(key)

    def add_to_all_show_keys(self, key, order=DEFAULT_ORDER):
        scene = self.scene
        if scene:
            if key not in scene['normal']:
                scene['normal'][key] = order

    def _process_lst(self, lst):
        return lst

    def get_view_data(self, get_type=False, scene_words=None):
        lst = self.get_view_data_list(get_type, scene_words=scene_words)
        ret = OrderedDict()
        for each in lst:
            ret[each['name']] = each.get('type')
        return ret

    def get_view_data_list(self, get_type=False, scene_words=None):
        self.has_type_keys = set()
        ret = []
        ret += self._get_builtin_field_list()
        ret += self._get_reverse_fk_field_list()
        ret += self._get_option_field_list()
        custom_ret = self._get_custom_field_list()
        ret_map = OrderedDict([(_.get("name"), _) for _ in ret])
        custom_ret_map = OrderedDict([(_.get("name"), _) for _ in custom_ret])
        for key, value in custom_ret_map.items():
            if key in ret_map:
                ret_map[key]["type"].update(value.get("type"))
                del custom_ret_map[key]
        ret = ret_map.values()
        ret += custom_ret_map.values()
        self.has_type_keys.update(_['name'] for _ in ret)
        ret += self._get_nontype_keys()
        if not get_type:
            ret = [_ for _ in ret if _['name'] not in self.never_show_keys]
            ret = self._orderby_scene_keys(ret, scene_words=scene_words)

        ret = self._process_ret(ret)
        ret = self._process_add_kwargs(ret)
        return ret


    def _get_custom_field_list(self):
        return [{
            "name": key,
            "type": type,
        } for key, type in self.key_map_type.items()]

    def register_required_keys(self, keys):
        if hasattr(keys, '__iter__'):
            self.required_keys |= set(keys)
        else:
            self.required_keys |= {keys}

    def _can_show_in_secne(self, show_scene):
        if type(show_scene) == bool:
            return show_scene
        return (show_scene & self.show_scene) != 0

    def _get_fields_options(self, fields):
        from mirrors.common.options import _get_options
        from mirrors.common import utils

        option_key_map = {}
        for field in fields:
            if field.option_key:
                for key in field.option_key.split(','):
                    option_key_map.setdefault(key, []).append(field)

        field_options = {}
        if not option_key_map:
            return field_options

        options = _get_options({
            'type__in': option_key_map.keys(),
            'is_deleted': False,
        })

        groupby_opts = utils.groupby_sorted_dict(options, 'type')
        for opt_type, options in groupby_opts:
            options = list(options)
            fields = option_key_map[opt_type]
            for field in fields:
                opt_list = field_options.setdefault(field, [])
                opt_list.extend(options)
        return field_options
    
    def _get_builtin_field_list(self):
        from mirrors.common.options import field_to_view_type
        if not self.model:
            return []
        meta = self.model._meta
        fields = meta.get_fields()

        result = []
        field_options = self._get_fields_options(fields)
        for each in fields:
            if self._can_show_in_secne(each.show) or each.name == 'id':
                view_info = field_to_view_type(each, meta, field_options)
                result.append({"name": each.name, "type": view_info})
        return result

    def _get_reverse_fk_field_list(self):

        return [{
            "name": key,
            "type": {
                "type": "reverse_foreignkey",
                "meta_class": {
                    "meta": "reverse_foreignkey",
                    "type_data": each['model'].__name__.lower(),
                },
            },
        } for key, each in self.reverse_fk_patch_info.items()]

    def get_service(self):
        raise NotImplementedError

    def _get_option_field_list(self):
        from mirrors.common.options import get_options
        ret = []
        for key, option_data in self.option_map.items():
            type = option_data.get('type', "optiondropdown")
            ret.append({
                "name": key,
                "type": {
                    "type": type,
                    "meta_class": {
                        "meta": type,
                        "type_data": get_options(option_data['option']),
                    },
                },
            })
        return ret

    def add_never_show_key(self, *keys):
        self.never_show_keys.update(keys)

    def add_avaible_reverse_fk_models(self, reverse_fk_info_list, **kwargs):
        if reverse_fk_info_list == ALL_REVERSE_FK_MODELS:
            if not self.model:
                raise AttributeError(
                    "Set All Reverse FK Models Need self.model exists:{}".
                    format(self.model_name),)
            reverse_fk_info_list = self.model._meta.reverse_relations.values()

        for info in reverse_fk_info_list:
            if not isinstance(info, dict):
                info = {"model": info}

            if not info.get('name'):
                name = info['model'].__name__.lower() + '_set'
            else:
                name = info['name']
                del info['name']

            if name not in self.reverse_fk_patch_info:
                self.reverse_fk_patch_info[name] = info

            self.process_control_able_kwargs(name, **kwargs)

    def modify_editable(self, key, editable, disable_export=False):
        self.key_map_type.setdefault(key, {})
        self.key_map_type[key].update({
            'editable': editable,
            'disable_export': disable_export,
        })

    def process_control_able_kwargs(self, name, **kwargs):
        self.control_able.setdefault(name, {})
        self.control_able[name].update(kwargs)

    def add_view_type(self, key, type, **kwargs):
        if isinstance(type, str):
            if isinstance(key, str):
                key = [key]

            for item in key:
                self.key_map_type[item] = {"type": type}
                self.process_control_able_kwargs(item, **kwargs)

        elif isinstance(type, dict):
            if type.get('type_data'):
                self.key_map_type[key] = {
                    "meta_class": {
                        "meta": type["type"],
                        "type_data": type["type_data"],
                        "leaf": type.get('leaf', False),
                    },
                    "type": type["type"],
                }
            elif type.get("option"):
                option_type = type.get('type') or "optiondropdown"
                ret = {
                    "option": type.get("option"),
                    "type": option_type,
                }
                self.option_map[key] = ret
            else:
                self.key_map_type[key] = type

            self.process_control_able_kwargs(key, **kwargs)

    def register_view_key(self, key, **kwargs):
        if key not in self.registered_key:
            self.registered_key.append(key)
        self.process_control_able_kwargs(key, **kwargs)

    def __unicode__(self):
        return '{0}.{1}'.format(self.__class__.__name__, self.model_name)



class CustomRegister(object):

    def __init__(self, manager):
        self.model_manager = manager
        self.manager = manager
        self.model_name = manager.model_name
        self.model = manager.model

    def __getattr__(self, item):
        return getattr(self.model_manager, item)

    @property
    def api(self):
        from mirrors.api import api
        return api._registry[self.model]

    def reg_after_import(self, func):
        self.model_manager.reg_after_import = func


class BaseLoader(object):
    ModelManagerCls = BaseModelManager
    RegCls = CustomRegister
    dir_path = None

    def __init__(self, host=None):
        lru_len = 70
        self.model_manager_map = {}
        self.host = host

    def get_model_manager(self, model_name):
        if model_name and not isinstance(model_name, str):
            model_name = model_name.__name__.lower()
        if model_name not in self.model_manager_map:
            self.try_import(model_name)
            model_manager = self.model_manager_map[model_name]
            self.model_manager_map[model_name] = model_manager
        return self.model_manager_map[model_name]

    def try_import(self, model_name):
        dir_path = self.dir_path
        model_manager = self.ModelManagerCls(model_name)
        self.model_manager_map[model_name] = model_manager
        self.on_imported(model_name, model_manager)
        for path in self.get_parent_path():
            self.import_by_path(model_name, dir_path, path, model_manager)
        self.after_import(model_name, model_manager)

    def import_by_path(self, model_name, dir_path, path, model_manager):
        return self._import_by_path(model_name, dir_path, path, model_manager)

    def get_base_model_names(self, model):
        from django.db import models
        """
            base_model_names, 在这里是FlowModel, FeedbackModel等。
        """
        if model and hasattr(model, '__bases__'):
            base_model_names = [
                each.__name__.lower()
                for each in model.__bases__
                if each not in (models.Model)
            ]
        else:
            base_model_names = []
        return base_model_names

    def _import_by_path(self, model_name, dir_path, path, model_manager):
        from mirrors.models import get_model_by_name
        # 有些model_name比如说capi，是不存在对应的model的。
        model = get_model_by_name(model_name) or getattr(
            model_manager,
            'model',
            None,
        )
        base_model_names = self.get_base_model_names(model)
        base_model_names.append(model_name)
        for file_name in base_model_names:
            from mirrors.libs.utils.resource import safe_import
            import_module = safe_import(file_name, dir_path, path)
            self.process_module(import_module, model_manager)
        return model_manager

    def process_module(self, module, model_manager):
        if module and getattr(module, 'run', None):
            module.run(self.RegCls(model_manager))

    def on_imported(self, model_name, model_manager):
        pass

    def after_import(self, model_name, model_manager):
        after_import = getattr(model_manager, 'reg_after_import', None)
        if after_import:
            after_import()

    @classmethod
    def get_parent_path(cls):
        from mirrors.libs.utils import build_module_path
        from django.conf import settings
        code = settings.CLIENT_CONFIG.get('CLIENT_CODE')
        return build_module_path(code)


class LoaderService(object):
    __metaclass__ = Singleton

    manager_cls = None

    def __init__(self):
        self._base_manager = self.manager_cls()
        self._custom_code_host = {"localhost:8000"}
        self._host_context = {}

    @property
    def manager(self):
        host = '127.0.0.1:8000'
        manager = self._host_context.get(host)
        if manager:
            return manager
        else:
            manager = self.manager_cls(host)
            self._host_context[host] = manager
            return manager

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls()
        return cls._instance

    def reload(self):
        self._host_context = {}
