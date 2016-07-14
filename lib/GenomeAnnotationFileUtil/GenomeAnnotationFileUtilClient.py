############################################################
#
# Autogenerated by the KBase type compiler -
# any changes made here will be overwritten
#
############################################################

from __future__ import print_function
# the following is a hack to get the baseclient to import whether we're in a
# package or not. This makes pep8 unhappy hence the annotations.
try:
    # baseclient and this client are in a package
    from .baseclient import BaseClient as _BaseClient  # @UnusedImport
except:
    # no they aren't
    from baseclient import BaseClient as _BaseClient  # @Reimport


class GenomeAnnotationFileUtil(object):

    def __init__(
            self, url=None, timeout=30 * 60, user_id=None,
            password=None, token=None, ignore_authrc=False,
            trust_all_ssl_certificates=False,
            auth_svc='https://kbase.us/services/authorization/Sessions/Login'):
        if url is None:
            raise ValueError('A url is required')
        self._service_ver = None
        self._client = _BaseClient(
            url, timeout=timeout, user_id=user_id, password=password,
            token=token, ignore_authrc=ignore_authrc,
            trust_all_ssl_certificates=trust_all_ssl_certificates,
            auth_svc=auth_svc)

    def genbank_to_genome_annotation(self, params, context=None):
        """
        :param params: instance of type "GenbankToGenomeAnnotationParams"
           (file_path or shock_id -- Local path or shock_id of the uploaded
           file with genome sequence in GenBank format or zip-file with
           GenBank files. genome_name -- The name you would like to use to
           reference this GenomeAnnotation. If not supplied, will use the
           Taxon Id and the data source to determine the name. taxon_wsname -
           name of the workspace containing the Taxonomy data, defaults to
           'ReferenceTaxons') -> structure: parameter "file_path" of String,
           parameter "shock_id" of String, parameter "ftp_url" of String,
           parameter "genome_name" of String, parameter "workspace_name" of
           String, parameter "source" of String, parameter "taxon_wsname" of
           String, parameter "convert_to_legacy" of type "boolean" (A boolean
           - 0 for false, 1 for true. @range (0, 1))
        :returns: instance of type "GenomeAnnotationDetails" -> structure:
        """
        return self._client.call_method(
            'GenomeAnnotationFileUtil.genbank_to_genome_annotation',
            [params], self._service_ver, context)

    def genome_annotation_to_genbank(self, params, context=None):
        """
        :param params: instance of type "GenomeAnnotationToGenbankParams"
           (genome_ref -- Reference to the GenomeAnnotation or Genome object
           in KBase in any ws supported format OR genome_name +
           workspace_name -- specifiy the genome name and workspace name of
           what you want.  If genome_ref is defined, these args are ignored.
           new_genbank_file_name -- specify the output name of the genbank
           file save_to_shock -- set to 1 or 0, if 1 then output is saved to
           shock. default is zero) -> structure: parameter "genome_ref" of
           String, parameter "genome_name" of String, parameter
           "workspace_name" of String, parameter "new_genbank_file_name" of
           String, parameter "save_to_shock" of type "boolean" (A boolean - 0
           for false, 1 for true. @range (0, 1))
        :returns: instance of type "GenbankFile" -> structure: parameter
           "path" of String, parameter "shock_id" of String
        """
        return self._client.call_method(
            'GenomeAnnotationFileUtil.genome_annotation_to_genbank',
            [params], self._service_ver, context)
