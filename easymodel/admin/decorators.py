from django.contrib.admin.options import BaseModelAdmin
from django.contrib.admin.util import flatten_fieldsets
from django.contrib.contenttypes.generic import generic_inlineformset_factory, BaseGenericInlineFormSet
from django.db.models.base import ModelBase

from easymodel.admin import forms
from easymodel.admin.generic import LocalizableGenericInlineFormSet
from easymodel.utils.languagecode import get_all_language_codes, localize_fieldnames, get_real_fieldname


__all__ = ('L10n', 'lazy_localized_list')

def compute_prohibited(fields, exclude, localized):
    return set(fields) - set(exclude) - set(localized)

class lazy_localized_list(list):
    """
    A descriptor that can get passed contrib.admin.validation.check_isseq
    undetected. It will give the 'real' name of an internationalized
    property when localized.
    """

    def __new__(cls, sequence, localized_fieldnames):
        if type(sequence) is lazy_localized_list:
            return sequence
        return list.__new__(cls, sequence)
        
    def __init__(self, sequence, localized_fieldnames):
        self.localized_fieldnames = localized_fieldnames
        super(lazy_localized_list, self).__init__(sequence)
    
    def __get__(self, obj, typ=None):
        """
        returns a localized version of the list this descriptor
        was initialized with.
        """
        return localize_fieldnames(self, self.localized_fieldnames)

class L10n(object):
    """
    Localise the admin class.
    
    filter fields to be displayed on a modeladmin class.
    All extra fields generated by I18n decorator should be hidden.
    Also uses a special form class that shows the field in the
    current language.
    
    This decorator also adds the 'can_edit_global_fields' permission to
    the model, only users that have this permission can actually edit fields
    that are not localised.
    
    >>> from easymodel.admin import L10n
    >>> @L10n(SomeModel)
    >>> class SomeModelAdmin(admin.ModelAdmin):
    >>>     pass
    
    or you can also:
    
    >>> admin.site.register(SomeModel,L10n(SomeModel, admin.ModelAdmin))
    
    This is usefull if you are using the same admin class for multiple models.
    
    If you have defined the model property on your admin class you can just
    leave it at:
    
    >>> @L10n
    >>> class SomeModelAdminWithModelDefined(admin.ModelAdmin):
    >>>     model = SomeModel
    """
    
    error_no_model = "L10n: %s does not have model defined, but no model was passed to L10n either"
    
    def __new__(typ, model_or_admin=None, cls=None):
        """
        Construct object and if cls is passed as well apply the object to that 
        immediately. This makes this decorator a factory as well.
        """
        inline_syntax = True if cls is not None else False
        
        obj = object.__new__(typ)
        
        if isinstance(model_or_admin, ModelBase):
            # if model_or_admin is a model class set the model.
            obj.model = model_or_admin
        elif issubclass(model_or_admin, BaseModelAdmin):
            # if model_or_admin is an admin class, model MUST be defined on that class.
            if hasattr(model_or_admin, 'model'):
                obj.model = model_or_admin.model
                # set cls to the admin class
                cls = model_or_admin
            else:
                raise(AttributeError(L10n.error_no_model % model_or_admin.__name__))
        else:
            raise TypeError("L10n can not accept parameters of type %s" % model_or_admin.__name__)
        
        # when using inline syntax we need a new type, otherwise we could modify django's ModelAdmin!
        # inline_syntax is using L10n as: L10n(ModelAdmin, Model)
        if inline_syntax:
            descendant = type(obj.model.__name__ + cls.__name__, (cls,), {'model':obj.model})
            return obj.__call__(descendant)
        elif cls: # if cls is defined call __call__ to localize admin class.
            if not hasattr(cls, 'model'):
                assert hasattr(obj, 'model'), "obj 'always' has a model because it was assigned 10 lines ago."
                setattr(cls, 'model', obj.model)
            
            return obj.__call__(cls)
            
        return obj
    
    def __call__(self, cls):
        """run the filter on the class to be decorated"""
        if hasattr(cls, 'model'):
            self.model = cls.model
        elif not self.model:
            raise AttributeError(L10n.error_no_model % (cls.__name__) )

        # gather names of fields added by I18n
        added_fields = []
        for field in self.model.localized_fields:
            for language in get_all_language_codes():
                added_fields.append(get_real_fieldname(field, language))

        # hide added fields from form and admin
        cls.exclude = added_fields
        cls.form = forms.make_localised_form(self.model, cls.form, exclude=added_fields)

        # determine name of the permission to edit untranslated fields
        permisson_name = "%s.can_edit_untranslated_fields_of_%s" % (
            self.model._meta.app_label, self.model.__name__.lower()
        )
        
        # make sure that fields become read_only when no permission is given.
        def get_readonly_fields(self, request, obj=None):
            if not request.user.has_perm(permisson_name):
                fields = self.fields or map(lambda x: x.name, self.model._meta.fields)
                # remove primary key because we don't show that, not even uneditable
                fields.pop(self.model._meta.pk_index())
                prohibited_fields = compute_prohibited(fields, self.exclude, self.model.localized_fields)
                
                return set(self.readonly_fields).union(prohibited_fields)
            
            return self.readonly_fields
        
        cls.get_readonly_fields = get_readonly_fields
        
        # override some views to hide fields which are not localized
        if hasattr(cls, 'change_view'):
            # BaseModelAdmin.__init__ will mess up our lazy lists if the following is
            # not allready defined
            if 'action_checkbox' not in cls.list_display and cls.actions is not None:
                cls.list_display = ['action_checkbox'] +  list(cls.list_display)
            
            if not cls.list_display_links:
                for name in cls.list_display:
                    if name != 'action_checkbox':
                        cls.list_display_links = [name]
                        break

            # Make certain properties lazy and internationalized
            cls.list_display_links = lazy_localized_list(cls.list_display_links, self.model.localized_fields)
            cls.list_display = lazy_localized_list(cls.list_display, self.model.localized_fields)
            cls.list_editable = lazy_localized_list(cls.list_editable, self.model.localized_fields)
            cls.search_fields = lazy_localized_list(cls.search_fields, self.model.localized_fields)
            
        else:
            def get_formset(self, request, obj=None, **kwargs):
                if self.declared_fieldsets:
                    fields = flatten_fieldsets(self.declared_fieldsets)
                else:
                    fields = None
                if self.exclude is None:
                    exclude = []
                else:
                    exclude = list(self.exclude)
                exclude.extend(self.get_readonly_fields(request, obj))
                exclude = exclude or None

                if not hasattr(self, 'ct_fk_field'):
                    return super(cls, self).get_formset(request, obj, **kwargs)
                else:
                    # TODO:
                    # this code can be deleted if django fixes GenericInlineModelAdmin it's
                    # get_formset signature so it looks like InlineModelAdmin
                    defaults = {
                        "ct_field": self.ct_field,
                        "fk_field": self.ct_fk_field,
                        "form": self.form,
                        "formfield_callback": self.formfield_for_dbfield,
                        "formset": self.formset,
                        "extra": self.extra,
                        "can_delete": self.can_delete,
                        "can_order": False,
                        "fields": fields,
                        "max_num": self.max_num,
                        "exclude": exclude
                    }
                    
                    defaults.update(kwargs)
                    # the BaseGenericInlineFormSet does not work too well
                    # with modified models, so use LocalizableGenericInlineFormSet.
                    if self.formset is BaseGenericInlineFormSet \
                        or self.formset.__class__ is BaseGenericInlineFormSet:
                        defaults['formset'] = LocalizableGenericInlineFormSet
                        
                    return generic_inlineformset_factory(self.model, **defaults)
            
            cls.get_formset = get_formset
        
            
        return cls
