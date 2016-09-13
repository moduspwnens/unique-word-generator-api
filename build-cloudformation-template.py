#!/usr/bin/env python

from __future__ import print_function

import os, sys, json

# These limits are set by CloudFormation.
function_max_characters = 4096
cloudformation_template_max_size = 460800 # Max for template loaded from S3

input_word_list_separator = "\n"
output_word_list_separator = "\n"

function_name_source_map = {
    "ConfigurationSetupFunction": "initial_configuration.py",
    "QueueRefreshFunction": "refresh_queue_messages.py",
    "WordGeneratorFunction": "generate_word.py",
    "PreWarmApiFunction": "prewarm_api.py",
    "WordListTableTriggerFunction": "word_list_table_trigger.py"
}

web_resource_name_source_map = {
    "WordGeneratorApiRootGet": "index.html"
}

word_lists_directory_name = "word-lists"
function_source_directory_name = "functions"
web_source_directory_name = "web"
cloudformation_source_template_file_name = "unique-word-api-source.json"

repository_directory_path = os.path.dirname(os.path.realpath(__file__))


'''
    LOAD CLOUDFORMATION SOURCE TEMPLATE
'''
cloudformation_source_template_file_path = os.path.join(
    repository_directory_path,
    cloudformation_source_template_file_name
)

cloudformation_source_template_string = None

try:
    cloudformation_source_template_string = open(cloudformation_source_template_file_path).read()
except:
    raise Exception("Unable to read CloudFormation source template at {}.".format(cloudformation_source_template_file_path))

cloudformation_template_object = None

try:
    cloudformation_template_object = json.loads(cloudformation_source_template_string)
except:
    raise Exception("Error decoding JSON from CloudFormation source template at {}.".format(cloudformation_source_template_file_path))



'''
    LOAD WEB SOURCE CODE
'''
web_resource_names = web_resource_name_source_map.keys()

for each_web_resource_name in web_resource_names:
    each_web_resource_file_name = web_resource_name_source_map[each_web_resource_name]
    
    web_resource_file_path = os.path.join(
        repository_directory_path,
        web_source_directory_name,
        each_web_resource_file_name
    )
    
    web_resource_source_string = None
    try:
        web_resource_source_string = open(web_resource_file_path).read()
    except:
        raise Exception("Unable to read web content source for {} at {}.".format(each_web_resource_name, web_resource_file_path))
    
    try:
        cloudformation_template_object["Resources"][each_web_resource_name]["Properties"]["Integration"]["IntegrationResponses"][0]["ResponseTemplates"]["text/html"] = web_resource_source_string
    except:
        raise Exception("Unable to add web content for {} to CloudFormation template.".format(each_web_resource_name))
    
    print("Web content for {} loaded into CloudFormation template.".format(each_web_resource_name), file=sys.stderr)



'''
    LOAD LAMBDA FUNCTION SOURCE CODE
'''
function_names = function_name_source_map.keys()

for each_function_name in function_names:
    each_function_source_file_name = function_name_source_map[each_function_name]
    
    function_source_file_path = os.path.join(
        repository_directory_path,
        function_source_directory_name,
        each_function_source_file_name
    )
    
    function_source_string = None
    try:
        function_source_string = open(function_source_file_path).read()
    except:
        raise Exception("Unable to read source code for {} function at {}.".format(each_function_name, function_source_file_path))
    
    # Reduce character count by converting four space indents to tabs.
    function_source_string = function_source_string.replace("    ", "\t")
    
    if len(function_source_string) > function_max_characters:
        raise Exception("Source code for function {} is too long. It is {} characters long ({} max).".format(
            each_function_name,
            len(function_source_string),
            function_max_characters
        ))
    
    try:
        cloudformation_template_object["Resources"][each_function_name]["Properties"]["Code"] = {
            "ZipFile": function_source_string
        }
    except:
        raise Exception("Unable to add source code for {} to CloudFormation template.".format(each_function_name))
    
    print("Code for {} loaded into CloudFormation template.".format(each_function_name), file=sys.stderr)



'''
    LOAD WORD LIST
'''
word_lists_directory_path = os.path.join(
    repository_directory_path,
    word_lists_directory_name
)

word_list_file_names = None

for (dir_path, dir_names, file_names) in os.walk(word_lists_directory_path):
    if dir_path != word_lists_directory_path:
        continue
    
    word_list_file_names = file_names

if not word_list_file_names:
    raise Exception("Unable to find word lists in \"{}\" directory.".format(word_lists_directory_name))

user_selected_word_list_file_name = None

if len(word_list_file_names) == 1:
    print("Using word list: {}.".format(word_list_file_names[0]), file=sys.stderr)
    user_selected_word_list_file_name[word_list_file_names[0]]

if user_selected_word_list_file_name is None:

    print("Select a word list:", file=sys.stderr)

    for i, each_file_name in enumerate(word_list_file_names):
        print(" [{}] {}".format(i+1, each_file_name), file=sys.stderr)

    while user_selected_word_list_file_name is None:
        print("> ", end="", file=sys.stderr)
        user_input_text = raw_input("")
    
        try:
            user_selected_word_list_file_name = word_list_file_names[int(user_input_text)-1]
        except:
            print("Invalid selection.", file=sys.stderr)


    print("You selected {}.".format(user_selected_word_list_file_name), file=sys.stderr)

# Read in input word list.
input_word_list = open(os.path.join(word_lists_directory_path, user_selected_word_list_file_name)).read().strip().split(input_word_list_separator)

# Verify no words in the list are duplicates.
words_found_map = {}
for each_word in input_word_list:
    if each_word is None or each_word == "":
        continue
    elif each_word in words_found_map:
        raise Exception("Word \"{}\" appears more than once in input word list.".format(each_word))
    words_found_map[each_word] = True

clean_input_word_list = words_found_map.keys()
clean_input_word_list.sort()

# We don't need this map any more.
del words_found_map

print("Word list contains {} words.".format(len(clean_input_word_list)), file=sys.stderr)

output_word_list_string = output_word_list_separator.join(clean_input_word_list)

try:
    cloudformation_template_object["Mappings"]["StaticVariables"]["Main"]["WordList"] = output_word_list_string
except Exception as e:
    raise Exception("Unable to set new word list in CloudFormation template.")

del input_word_list
del clean_input_word_list
del output_word_list_string

print("Word list added to CloudFormation template successfully.", file=sys.stderr)

'''
    OUTPUT TEMPLATE
'''

# Try exporting in a friendly, readable format.
output_template_string = json.dumps(cloudformation_template_object, indent=4)
if len(output_template_string) > cloudformation_template_max_size:
    
    # If it's too big, try exporting in a JSON-minified format.
    output_template_string = json.dumps(cloudformation_template_object, separators=(',', ':'))
    
    if len(output_template_string) > cloudformation_template_max_size:
        raise Exception("Output CloudFormation template is too big at {} bytes (max: {}).".format(
            len(output_template_string),
            cloudformation_template_max_size
        ))

print(output_template_string)

if sys.stdout.isatty():
    print("", file=sys.stderr)
    print("To save the template, try piping the output of this script to a file.", file=sys.stderr)
    
    python_name = "python"
    if sys.version_info[0] > 2:
        python_name += sys.version_info[0]
    
    print("For example, \n    {} {} > new-cloudformation-template.json".format(
        python_name,
        " ".join(sys.argv)
    ), file=sys.stderr)
