"""
Change
======

Manage gerrit changes
"""

from gerrit.helper import decode_json
from gerrit.error import UnhandledError
from gerrit.projects.project import Project
from gerrit.changes.reviewer import Reviewer
from gerrit.changes.revision import Revision

class Change(object):
    """Manage gerrit changes"""

    def __init__(self, gerrit_con):
        self._gerrit_con = gerrit_con
        self.full_id = None

    def __getattr__(self, name):
        r_endpoint = "/a/changes/%s/" % self.full_id

        req = self._gerrit_con.call(r_endpoint=r_endpoint)

        status_code = req.status_code
        result = req.content.decode('utf-8')

        if status_code == 200:
            result = decode_json(result).get(name)
            if result is None:
                raise AttributeError
            else:
                return result
        else:
            raise AttributeError

    def get_change(self, project, branch, change_id):
        """
        Get ChangeInfo for a change
        :returns: Dict of the ChangeInfo for the change
        :rtype: dict
        :exception: ValueError, UnhandledError
        """
        if isinstance(project, Project):
            project = project.name

        if project == '':
            raise KeyError('Project required')

        if branch == '':
            raise KeyError('Branch required')

        if change_id == '':
            raise KeyError('Id required')

        # HTTP REST API HEADERS
        self.full_id = '%s~%s~%s' % (project, branch, change_id)
        self._gerrit_con = self._gerrit_con

        r_endpoint = "/a/changes/%s/" % self.full_id

        req = self._gerrit_con.call(r_endpoint=r_endpoint)

        status_code = req.status_code
        result = req.content.decode('utf-8')

        if status_code == 200:
            self.full_id = decode_json(result).get('id')
            return self
        elif status_code == 404:
            raise ValueError(result)
        else:
            raise UnhandledError(result)

    def create_change(self, project, subject, branch, options):
        """
        Create a change
        :param project: Project to create change in
        :type project: str or gerrit.project.Project
        :param subject: Subject of the change
        :type subject: str
        :param branch: The name of the target branch
        :type branch: str
        :param options: Additional options
        :type options: dict
        :returns: gerrit.change.Change object
        :rtype: gerrit.change.Change
        :except: UnhandledError
        """

        r_endpoint = "/a/changes/"

        if isinstance(project, Project):
            project = project.name

        data = {
            'project': project,
            'subject': subject,
            'branch': branch,
        }

        if options is None:
            options = {}

        for key in options.keys():
            data[key] = options[key]

        req = self._gerrit_con.call(
            request='post',
            r_endpoint=r_endpoint,
            r_payload=data,
        )

        result = req.content.decode('utf-8')

        if req.status_code == 201:
            self.full_id = "%s~%s~%s" % (
                project,
                branch,
                decode_json(result).get('change_id')
            )
            return self
        else:
            raise UnhandledError(result)

    def submit_change(self, options=None):
        """
        Submit the change
        :param options: Additional options
        :type options: dict
        :returns: On success, True
        :rtype: bool
        :except: UnhandledError
        """

        r_endpoint = "/a/changes/%s/submit" % self.full_id

        if options is None:
            options = {}

        req = self._gerrit_con.call(
            request='post',
            r_endpoint=r_endpoint,
            r_payload=options,
        )

        if req.status_code == 200:
            return True
        else:
            result = req.content.decode('utf-8')
            raise UnhandledError(result)

    def add_reviewer(self, account_id):
        """
        Add a reviewer to the change
        :param account_id: The user account that should be added as a reviewer
        :type account_id: str
        :returns: You get a True boolean type if the addition of this user was successful
        :rtype: bool
        :except: LookupError, AlreadyExists, UnhandledError
        """
        reviewer = Reviewer(self._gerrit_con, self.change_id)
        return reviewer.add_reviewer(account_id)

    def delete_reviewer(self, account_id):
        """
        Delete a reviewer from the change
        :param account_id: Remove a user with account-id as reviewer.
        :type account_id: str
        :returns: On success, True
        :rtype: bool
        :exception: error.AuthorizationError
        """
        reviewer = Reviewer(self._gerrit_con, self.change_id)
        return reviewer.delete_reviewer(account_id)

    def list_reviewers(self):
        """
        List reviewers for the change
        :returns: The reviews for the specified change-id at init
        :rtype: dict
        :exception: ValueError, UnhandledError
        """
        reviewer = Reviewer(self._gerrit_con, self.change_id)
        return reviewer.list_reviewers()

    def set_review(self, labels=None, message='', comments=None, revision='current'):
        """
        Create a review for the change and a specific patch set
        :param labels: This is used to set +2 Code-Review for example.
        :type labels: dict
        :param message: The message will appear in the actually change-request page.
        :type message: str
        :param comments: This will become comments in the code.
        :type comments: dict
        :returns: On success, True
        :rtype: bool
        """
        revision = Revision(self._gerrit_con, self.change_id, revision)
        return revision.set_review(labels=labels, message=message, comments=comments)
