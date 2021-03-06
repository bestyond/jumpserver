from common.exceptions import JMSException
from orgs.models import Organization
from .. import models


class ApplicationAttrsSerializerViewMixin:

    def get_serializer_class(self):
        serializer_class = super().get_serializer_class()
        app_type = self.request.query_params.get('type')
        app_category = self.request.query_params.get('category')
        type_options = list(dict(models.Category.get_all_type_serializer_mapper()).keys())
        category_options = list(dict(models.Category.get_category_serializer_mapper()).keys())

        # ListAPIView 没有 action 属性
        # 不使用method属性，因为options请求时为method为post
        action = getattr(self, 'action', 'list')

        if app_type and app_type not in type_options:
            raise JMSException(
                'Invalid query parameter `type`, select from the following options: {}'
                ''.format(type_options)
            )
        if app_category and app_category not in category_options:
            raise JMSException(
                'Invalid query parameter `category`, select from the following options: {}'
                ''.format(category_options)
            )

        if action in [
            'create', 'update', 'partial_update', 'bulk_update', 'partial_bulk_update'
        ] and not app_type:
            # action: create / update
            raise JMSException(
                'The `{}` action must take the `type` query parameter'.format(action)
            )

        if app_type:
            # action: create / update / list / retrieve / metadata
            attrs_cls = models.Category.get_type_serializer_cls(app_type)
        elif app_category:
            # action: list / retrieve / metadata
            attrs_cls = models.Category.get_category_serializer_cls(app_category)
        else:
            attrs_cls = models.Category.get_no_password_serializer_cls()
        return type('ApplicationDynamicSerializer', (serializer_class,), {'attrs': attrs_cls()})


class SerializeApplicationToTreeNodeMixin:

    @staticmethod
    def _serialize_db(db):
        return {
            'id': db.id,
            'name': db.name,
            'title': db.name,
            'pId': '',
            'open': False,
            'iconSkin': 'database',
            'meta': {'type': 'database_app'}
        }

    @staticmethod
    def _serialize_remote_app(remote_app):
        return {
            'id': remote_app.id,
            'name': remote_app.name,
            'title': remote_app.name,
            'pId': '',
            'open': False,
            'isParent': False,
            'iconSkin': 'chrome',
            'meta': {'type': 'remote_app'}
        }

    @staticmethod
    def _serialize_cloud(cloud):
        return {
            'id': cloud.id,
            'name': cloud.name,
            'title': cloud.name,
            'pId': '',
            'open': False,
            'isParent': False,
            'iconSkin': 'k8s',
            'meta': {'type': 'k8s_app'}
        }

    def _serialize_application(self, application):
        method_name = f'_serialize_{application.category}'
        data = getattr(self, method_name)(application)
        data.update({
            'pId': application.org.id,
            'org_name': application.org_name
        })
        return data

    def serialize_applications(self, applications):
        data = [self._serialize_application(application) for application in applications]
        return data

    @staticmethod
    def _serialize_organization(org):
        return {
            'id': org.id,
            'name': org.name,
            'title': org.name,
            'pId': '',
            'open': True,
            'isParent': True,
            'meta': {
                'type': 'node'
            }
        }

    def serialize_organizations(self, organizations):
        data = [self._serialize_organization(org) for org in organizations]
        return data

    @staticmethod
    def filter_organizations(applications):
        organizations_id = set(applications.values_list('org_id', flat=True))
        organizations = [Organization.get_instance(org_id) for org_id in organizations_id]
        return organizations

    def serialize_applications_with_org(self, applications):
        organizations = self.filter_organizations(applications)
        data_organizations = self.serialize_organizations(organizations)
        data_applications = self.serialize_applications(applications)
        data = data_organizations + data_applications
        return data
