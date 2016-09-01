from flask import jsonify
from uservice.views.basic_views import BasicProjectView


class ProjectStatus(BasicProjectView):
    """Get and create projects"""

    def _get_view(self, version, project):
        """Used to get project status"""
        return jsonify(Version=version, Project=project)

    def _put_view(self, version, project):
        """Used to create project"""
        return jsonify(Version=version, Project=project)

    def _delete_view(self, version, project):
        """Used to delete project"""
        self._get_database(project).drop()
        return jsonify(Version=version, Project=project)
