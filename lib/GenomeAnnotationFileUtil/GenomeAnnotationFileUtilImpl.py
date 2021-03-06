# -*- coding: utf-8 -*-
#BEGIN_HEADER

import os
import sys
import shutil
import traceback
import uuid
from pprint import pprint, pformat

from biokbase.workspace.client import Workspace

# utilities for unpacking things- could switch to functions in DataFileUtil when available
import biokbase.Transform.script_utils as script_utils

import trns_transform_Genbank_Genome_to_KBaseGenomeAnnotations_GenomeAnnotation as uploader
from DataFileUtil.DataFileUtilClient import DataFileUtil

# For Genome to genbank downloader
from doekbase.data_api.downloaders import GenomeAnnotation
from doekbase.data_api.annotation.genome_annotation.api import GenomeAnnotationAPI as GenomeAnnotationAPI

#END_HEADER


class GenomeAnnotationFileUtil:
    '''
    Module Name:
    GenomeAnnotationFileUtil

    Module Description:
    
    '''

    ######## WARNING FOR GEVENT USERS #######
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    #########################################
    VERSION = "0.0.1"
    GIT_URL = "https://github.com/rsutormin/GenomeAnnotationFileUtil"
    GIT_COMMIT_HASH = "1cb3d9e675e8965dc2e04b6290676ed5746fe28a"
    
    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.workspaceURL = config['workspace-url']
        self.shockURL = config['shock-url']
        self.handleURL = config['handle-service-url']
        self.sharedFolder = config['scratch']
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.services = {
            "workspace_service_url": self.workspaceURL,
            "shock_service_url": self.shockURL,
            "handle_service_url": self.handleURL
        }
        #END_CONSTRUCTOR
        pass
    

    def genbank_to_genome_annotation(self, ctx, params):
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
           parameter "genome_annotation_ref" of String
        """
        # ctx is the context object
        # return variables are: details
        #BEGIN genbank_to_genome_annotation

        print('genbank_to_genome_annotation -- paramaters = ')
        pprint(params)

        # validate input and set defaults.  Note that because we don't call the uploader method
        # as a stand alone script, we do the validation here.
        if 'workspace_name' not in params:
            raise ValueError('workspace_name field was not defined')
        workspace_name = params['workspace_name']

        if 'genome_name' not in params:
            raise ValueError('genome_name field was not defined')
        genome_name = params['genome_name']

        source = 'Genbank'
        if 'source' in params:
            source = source;

        taxon_wsname = 'ReferenceTaxons'
        if 'taxon_wsname' in params:
            taxon_wsname = params['taxon_wsname']

        # other options to handle
        # release
        # taxon_reference
        # exclude_feature_types
        # type


        # construct the input directory where we stage files
        input_directory =  os.path.join(self.sharedFolder, 'genome-upload-staging-'+str(uuid.uuid4()))
        os.makedirs(input_directory)

        # determine how to get the file: if it is from shock, download it.  If it
        # is just sitting there, then use it.  Move the file to the staging input directory

        genbank_file_path = None

        if 'file_path' not in params:
            if 'shock_id' not in params:
                if 'ftp_url' not in params:
                    raise ValueError('No input file (either file_path, shock_id, or ftp_url) provided')
                else:
                    # TODO handle ftp - this creates a directory for us, so update the input directory
                    print('calling Transform download utility: script_utils.download');
                    print('URL provided = '+params['ftp_url']);
                    script_utils.download_from_urls(
                            working_directory = input_directory,
                            token = ctx['token'], # not sure why this requires a token to download from a url...
                            urls  = {
                                        'ftpfiles': params['ftp_url']
                                    }
                        );
                    input_directory = os.path.join(input_directory,'ftpfiles')
                    # unpack everything in input directory
                    dir_contents = os.listdir(input_directory)
                    print('downloaded directory listing:')
                    pprint(dir_contents)
                    dir_files = []
                    for f in dir_contents:
                        if os.path.isfile(os.path.join(input_directory, f)):
                            dir_files.append(f)

                    print('processing files in directory...')
                    for f in dir_files:
                        # unpack if needed using the standard transform utility
                        print('unpacking '+f)
                        script_utils.extract_data(filePath=os.path.join(input_directory,f))

            else:
                # handle shock file
                dfUtil = DataFileUtil(self.callback_url, token=ctx['token'])
                file_name = dfUtil.shock_to_file({
                                    'file_path': input_directory,
                                    'shock_id': params['shock_id']
                                })['node_file_name']
                genbank_file_path = os.path.join(input_directory, file_name)
        else:
            # copy the local file to the input staging directory
            # (NOTE: could just move it, but then this method would have the side effect of moving your
            # file which another SDK module might have an open handle on)
            local_file_path = params['file_path']
            genbank_file_path = os.path.join(input_directory, os.path.basename(local_file_path))
            shutil.copy2(local_file_path, genbank_file_path)

        if genbank_file_path is not None:
            print("input genbank file =" + genbank_file_path)

            # unpack if needed using the standard transform utility
            script_utils.extract_data(filePath=genbank_file_path)

        # do the upload (doesn't seem to return any information)
        uploader.upload_genome(
                logger=None,

                shock_service_url = self.shockURL,
                handle_service_url = self.handleURL,
                workspace_service_url = self.workspaceURL,

                input_directory=input_directory,

                workspace_name   = workspace_name,
                core_genome_name = genome_name,
                source           = source,
                taxon_wsname     = taxon_wsname
            )

        #### Code to convert to legacy type if requested
        if 'convert_to_legacy' in params and params['convert_to_legacy']==1:
            from doekbase.data_api.converters import genome as cvt
            print('Converting to legacy type, object={}'.format(genome_name))
            cvt.convert_genome(
                    shock_url=self.shockURL,
                    handle_url=self.handleURL,
                    ws_url=self.workspaceURL,
                    obj_name=genome_name,
                    ws_name=workspace_name)

        # clear the temp directory
        shutil.rmtree(input_directory)

        # get WS metadata to return the reference to the object (could be returned by the uploader method...)
        ws = Workspace(url=self.workspaceURL)
        info = ws.get_object_info_new({'objects':[{'ref':workspace_name + '/' + genome_name}],'includeMetadata':0, 'ignoreErrors':0})[0]

        details = {
            'genome_annotation_ref':str(info[6]) + '/' + str(info[0]) + '/' + str(info[4])
        }


        #END genbank_to_genome_annotation

        # At some point might do deeper type checking...
        if not isinstance(details, dict):
            raise ValueError('Method genbank_to_genome_annotation return value ' +
                             'details is not type dict as required.')
        # return the results
        return [details]

    def genome_annotation_to_genbank(self, ctx, params):
        """
        :param params: instance of type "GenomeAnnotationToGenbankParams"
           (genome_ref -- Reference to the GenomeAnnotation or Genome object
           in KBase in any ws supported format OR genome_name +
           workspace_name -- specifiy the genome name and workspace name of
           what you want.  If genome_ref is defined, these args are ignored.
           new_genbank_file_name -- specify the output name of the genbank
           file, optional save_to_shock -- set to 1 or 0, if 1 then output is
           saved to shock. default is zero) -> structure: parameter
           "genome_ref" of String, parameter "genome_name" of String,
           parameter "workspace_name" of String, parameter
           "new_genbank_file_name" of String, parameter "save_to_shock" of
           type "boolean" (A boolean - 0 for false, 1 for true. @range (0, 1))
        :returns: instance of type "GenbankFile" -> structure: parameter
           "path" of String, parameter "shock_id" of String
        """
        # ctx is the context object
        # return variables are: file
        #BEGIN genome_annotation_to_genbank

        print('genome_annotation_to_genbank -- paramaters = ')
        pprint(params)

        service_endpoints = {
            "workspace_service_url": self.workspaceURL, 
            "shock_service_url": self.shockURL,
            "handle_service_url": self.handleURL
        }

        # parse/validate parameters.  could do a better job here.
        genome_ref = None
        if 'genome_ref' in params and params['genome_ref'] is not None:
            genome_ref = params['genome_ref']
        else:
            if 'genome_name' not in params:
                raise ValueError('genome_ref and genome_name are not defined.  One of those is required.')
            if 'workspace_name' not in params:
                raise ValueError('workspace_name is not defined.  This is required if genome_name is specified' +
                    ' without a genome_ref')
            genome_ref = params['workspace_name'] + '/' + params['genome_name']

        # do a quick lookup of object info- could use this to do some validation.  Here we need it to provide
        # a nice output file name if it is not set...  We should probably catch errors here and print out a nice
        # message - usually this would mean the ref was bad.
        ws = Workspace(url=self.workspaceURL)
        info = ws.get_object_info_new({'objects':[{'ref':genome_ref}],'includeMetadata':0, 'ignoreErrors':0})[0]
        print('resolved object to:');
        pprint(info)

        if 'new_genbank_file_name' not in params or params['new_genbank_file_name'] is None:
            new_genbank_file_name = info[1] + ".gbk"
        else:
            new_genbank_file_name = params['new_genbank_file_name']


        # construct a working directory to hand off to the data_api
        working_directory =  os.path.join(self.sharedFolder, 'genome-download-'+str(uuid.uuid4()))
        os.makedirs(working_directory)
        output_file_destination = os.path.join(working_directory,new_genbank_file_name)

        # do it
        print('calling: doekbase.data_api.downloaders.GenomeAnnotation.downloadAsGBK');
        GenomeAnnotation.downloadAsGBK(
                            genome_ref,
                            service_endpoints,
                            ctx['token'],
                            output_file_destination,
                            working_directory)

        # if we need to upload to shock, well then do that too.
        file = {}
        if 'save_to_shock' in params and params['save_to_shock'] == 1:
            dfUtil = DataFileUtil(self.callback_url, token=ctx['token'])
            file['shock_id'] =dfUtil.file_to_shock({
                                    'file_path':output_file_destination,
                                    'gzip':0,
                                    'make_handle':0
                                    #attributes: {} #we can set shock attributes if we want
                                })['shock_id']
        else:
            file['path'] = output_file_destination

        #END genome_annotation_to_genbank

        # At some point might do deeper type checking...
        if not isinstance(file, dict):
            raise ValueError('Method genome_annotation_to_genbank return value ' +
                             'file is not type dict as required.')
        # return the results
        return [file]

    def export_genome_annotation_as_genbank(self, ctx, params):
        """
        A method designed especially for download, this calls 'genome_annotation_to_genbank' to do
        the work, but then packages the output with WS provenance and object info into
        a zip file and saves to shock.
        :param params: instance of type "ExportParams" -> structure:
           parameter "input_ref" of String
        :returns: instance of type "ExportOutput" -> structure: parameter
           "shock_id" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN export_genome_annotation_as_genbank

         # validate parameters
        if 'input_ref' not in params:
            raise ValueError('Cannot export GenomeAnnotation- not input_ref field defined.')

        # get WS metadata to get ws_name and obj_name
        ws = Workspace(url=self.workspaceURL)
        info = ws.get_object_info_new({'objects':[{'ref': params['input_ref'] }],'includeMetadata':0, 'ignoreErrors':0})[0]

        # export to a file
        file = self.genome_annotation_to_genbank(ctx, { 
                            'genome_ref': params['input_ref'], 
                            'new_genbank_file_name': info[1]+'.gbk' })[0]

        # create the output directory and move the file there
        export_package_dir = os.path.join(self.sharedFolder, info[1])
        os.makedirs(export_package_dir)
        shutil.move(file['path'], os.path.join(export_package_dir, os.path.basename(file['path'])))

        # package it up and be done
        dfUtil = DataFileUtil(self.callback_url)
        package_details = dfUtil.package_for_download({
                                    'file_path': export_package_dir,
                                    'ws_refs': [ params['input_ref'] ]
                                })

        output = { 'shock_id': package_details['shock_id'] }

        #END export_genome_annotation_as_genbank

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method export_genome_annotation_as_genbank return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def load_new_genome_data(self, ctx, params):
        """
        :param params: instance of type "LoadNewGenomeDataParams" ->
           structure: parameter "genome_ref" of String
        :returns: instance of type "GenomeData" (scientific_name - scientific
           name of the organism. taxonomy_id - NCBI taxonomic id of the
           organism. kingdom - taxonomic kingdom of the organism.
           scientific_lineage - scientific lineage of the organism.
           genetic_code - scientific name of the organism. organism_aliases -
           aliases for the organism associated with this GenomeAnnotation.
           assembly_source - source organization for the Assembly.
           assembly_source_id - identifier for the Assembly used by the
           source organization. assembly_source_date - date of origin the
           source indicates for the Assembly. gc_content - GC content for the
           entire Assembly. dna_size - total DNA size for the Assembly.
           num_contigs - number of contigs in the Assembly. contig_ids -
           contig identifier strings for the Assembly. external_source - name
           of the external source. external_source_date - date of origin the
           external source indicates for this GenomeAnnotation. release -
           release version for this GenomeAnnotation data.
           original_source_filename - name of the file used to generate this
           GenomeAnnotation. feature_type_counts - number of features of each
           type.) -> structure: parameter "scientific_name" of String,
           parameter "taxonomy_id" of Long, parameter "kingdom" of String,
           parameter "scientific_lineage" of list of String, parameter
           "genetic_code" of Long, parameter "organism_aliases" of list of
           String, parameter "assembly_source" of String, parameter
           "assembly_source_id" of String, parameter "assembly_source_date"
           of String, parameter "gc_content" of Double, parameter "dna_size"
           of Long, parameter "num_contigs" of Long, parameter "contig_ids"
           of list of String, parameter "external_source" of String,
           parameter "external_source_date" of String, parameter "release" of
           String, parameter "original_source_filename" of String, parameter
           "feature_type_counts" of mapping from String to Long, parameter
           "features" of list of type "FeatureData" (feature_id - identifier
           for this feature feature_type - the Feature type e.g., "mRNA",
           "CDS", "gene", ... feature_function - the functional annotation
           description feature_aliases - dictionary of Alias string to List
           of source string identifiers feature_dna_sequence_length - integer
           representing the length of the DNA sequence for convenience
           feature_dna_sequence - string containing the DNA sequence of the
           Feature feature_md5 - string containing the MD5 of the sequence,
           calculated from the uppercase string feature_locations - list of
           Feature regions, where the Feature bounds are calculated as
           follows: - For "+" strand, [start, start + length) - For "-"
           strand, (start - length, start] feature_publications - ist of any
           known publications related to this Feature
           feature_quality_warnings - list of strings indicating known data
           quality issues (note: not used for Genome type, but is used for
           GenomeAnnotation) feature_quality_score - quality value with
           unknown algorithm for Genomes, not calculated yet for
           GenomeAnnotations. feature_notes - notes recorded about this
           Feature feature_inference - inference information) -> structure:
           parameter "feature_id" of String, parameter "feature_type" of
           String, parameter "feature_function" of String, parameter
           "feature_aliases" of mapping from String to list of String,
           parameter "feature_dna_sequence_length" of Long, parameter
           "feature_dna_sequence" of String, parameter "feature_md5" of
           String, parameter "feature_locations" of list of type "Region"
           (contig_id - the identifier for the contig to which this region
           corresponds. strand - either a "+" or a "-", for the strand on
           which the region is located. start - starting position for this
           region. length - distance from the start position that bounds the
           end of the region.) -> structure: parameter "contig_id" of String,
           parameter "strand" of String, parameter "start" of Long, parameter
           "length" of Long, parameter "feature_publications" of list of
           String, parameter "feature_quality_warnings" of list of String,
           parameter "feature_quality_score" of list of String, parameter
           "feature_notes" of String, parameter "feature_inference" of
           String, parameter "protein" of type "ProteinData" (protein_id -
           protein identifier, which is feature ID plus ".protein"
           protein_amino_acid_sequence - amino acid sequence for this protein
           protein_function - function of protein protein_aliases - list of
           aliases for the protein protein_md5 - MD5 hash of the protein
           translation (uppercase)) -> structure: parameter "protein_id" of
           String, parameter "protein_amino_acid_sequence" of String,
           parameter "protein_function" of String, parameter
           "protein_aliases" of list of String, parameter "protein_md5" of
           String, parameter "protein_domain_locations" of list of String
        """
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN load_new_genome_data
        genome_ref = params['genome_ref']
        ga = GenomeAnnotationAPI(self.services, ctx['token'], genome_ref)
        feature_types = ga.get_feature_types()
        feature_ids_by_type = ga.get_feature_ids({"type_list": feature_types})
        feature_ids = []
        feature_id_map = feature_ids_by_type['by_type']
        for feature_type in feature_id_map:
            feature_ids.extend(feature_id_map[feature_type])
        feature_map = ga.get_features(feature_ids)
        protein_map = ga.get_proteins()
        features = []
        proteins = []
        for feature_id in feature_map:
            feature = feature_map[feature_id]
            if feature_id in protein_map:
                protein = protein_map[feature_id]
                feature['protein'] = protein
                proteins.append(protein)
            features.append(feature)
        #genome_data = ga.get_summary()    # It returnes None !!! Maybe something wasn't prepared at the end of upload from Genbank?
        # Temporary load genome summary from directly from Workspace (there are some fields not present)
        ws = Workspace(url=self.workspaceURL)
        genome_data = ws.get_objects([{"ref": genome_ref}])[0]["data"]
        genome_data.pop('publications', None)
        genome_data.pop('feature_lookup', None)
        if 'scientific_name' not in genome_data and 'display_sc_name' in genome_data:
            genome_data['scientific_name'] = genome_data['display_sc_name']
        genome_data['features'] = features
        returnVal = genome_data
        #END load_new_genome_data

        # At some point might do deeper type checking...
        if not isinstance(returnVal, dict):
            raise ValueError('Method load_new_genome_data return value ' +
                             'returnVal is not type dict as required.')
        # return the results
        return [returnVal]

    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK", 'message': "", 'version': self.VERSION, 
                     'git_url': self.GIT_URL, 'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
