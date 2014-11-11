#!/usr/bin/python
# -*- ecoding:utf-8 -*-

import datetime
import urllib2
import json
import argparse
import os

LIST = "list"
OBJCET = "obj"
STRING = "String"
INT = "int"
DOUBLE = "double"
BOOLEAN = "boolean"

TODO = "TODO"

DEFAULT_INTERFACES = ['BaseType']

INTERFACES = {
}

DEFAULT_CLASS_IMPORTS = [
]

CLASS_IMPORTS = {
}

PACKAGE = "//TODO ";

# 'http://192.168.1.172:89/company/getCompanyInfo/user_code/5c57eab3600e11e48da914dae974c66c/company_code/5c57f114600e11e48da914dae974c66c'
def main():
    arg = args();
    url = arg.url

    if not url:
        print "please input --url, specify The need for automatic generation of the class interface,Must be a JSON structure"
        exit()
    
    className = arg.className
	
    if not className:
		print "please input --className, specify root class name" 
		exit()

    outPath = arg.outPath
    global PACKAGE 
    PACKAGE = arg.package

    
    if not os.path.exists(outPath):
        outPath = os.getcwd()
    
    outType = arg.outType
    
    httpConn = urllib2.urlopen(url)
    content = httpConn.read()
    jsondata = json.loads(content)
    
    if isinstance(jsondata, (list)):
        jsondata = jsondata[0]
        
    attributes = parserAttributes(className, jsondata);
    for key, value in attributes.iteritems():
        #
        content = GenerateClass_bean(key, value, outType == 2)
        fileName = key + ".java"
        print "creating... " + fileName;
        typePath = os.path.join(outPath, 'type');
        if not os.path.exists(typePath):
            os.mkdir(typePath)
        fileName = os.path.join(typePath, fileName)
        writJava(fileName, content)
        
        if outType == 1:
            # parser
            parserFileName = key + "Parser.java"
            print "creating... " + parserFileName;
            parserContent = GenerateClass_parser(key, value);
            parserPath = os.path.join(outPath, 'parsers');
            if not os.path.exists(parserPath):
                os.mkdir(parserPath)
            parserFileName = os.path.join(parserPath, parserFileName);
            writJava(parserFileName, parserContent)

def writJava(fileName, content):
    f = open(fileName, 'wb');
    f.write(content);
    f.close()

def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="parsed json url",type=str)
    parser.add_argument("--className", help="specify root class name")
    parser.add_argument("--outPath", default=os.getcwd(), help="Automatic generation of storage file path ,default current path.")
    parser.add_argument("--package", default=PACKAGE, help="Generating the .java file class package name")
    parser.add_argument("--outType", default=2, type=int, help=" 1: parser       2:Gson")
    return parser.parse_args()

################################################################################################

def parserAttributes(clazzName, jsondict, result={}):
    attributes = {}
    for key, value in jsondict.iteritems():
        
        if isinstance(value, (dict)):
            typ = ''.join([word.capitalize() for word in key.split('_')]);
            attributes.setdefault(key, (OBJCET, [typ]));
            parserAttributes(typ, value, result)
        elif isinstance(value, (list)):
            if len(value) > 0 :
                itemValue= value[0]
                # 是字典类型在去迭代
                if isinstance(itemValue, (dict)):
                    subTyp = ''.join([word.capitalize() for word in key.split('_')]);
                    parserAttributes(subTyp, itemValue, result)
                elif isinstance(value, (str, unicode)) :
                    subTyp = STRING
                elif isinstance(value, (int)) :
                    subTyp = STRING
                elif isinstance(value, (float)):
                    subTyp = STRING
                else :
                    subTyp = TODO
                typeList = "List<" + subTyp + ">"
                attributes.setdefault(key, (LIST, [typeList,subTyp]));
            else:
                # 没有数据添加TODO标记
                attributes.setdefault(key, (TODO, [TODO]));
                pass
        elif isinstance(value, (str, unicode)) :
            attributes.setdefault(key, (STRING, [STRING]));
        elif isinstance(value, (int)) :
            attributes.setdefault(key, (INT, [INT]));
        elif isinstance(value, (float)):
            attributes.setdefault(key, (DOUBLE, [DOUBLE]));
        else :
            attributes.setdefault(key, (TODO, [TODO]));
    result[clazzName] = attributes;
    return result


############################################################################################

HEADER = """\
/**
 * Copyright 2014 Galen Wu
 */

package %(package)s.type;

%(imports)s

/**
 * Auto-generated: %(timestamp)s
 *
 * @author Galen Wu (wuzhenlin135@126.com)
 */
public class %(type_name)s %(interfaces)s{
"""

# getter 
GETTER = """\
%(annotate)spublic %(attribute_type)s get%(camel_name)s() {
%(annotate)s    return %(field_name)s;
%(annotate)s}
"""
# setter 
SETTER = """\
%(annotate)spublic void set%(camel_name)s(%(attribute_type)s %(attribute_name)s) {
%(annotate)s    %(field_name)s = %(attribute_name)s;
%(annotate)s}
"""

# 布尔型get方法 ，没有get
BOOLEAN_GETTER = """\
%(annotate)spublic %(attribute_type)s %(attribute_name)s() {
%(annotate)s    return %(field_name)s;
%(annotate)s}
"""

# type_name 文件名。 attributes 字段名，类型
def GenerateClass_bean(type_name, attributes, isGson=False):
    lines = []
    # sorted(attributes):
    for attribute_name in sorted(attributes):
        typ, children = attributes[attribute_name]
        if typ == LIST or typ == OBJCET:
            typ = children[0]
        
        if isGson:
            lines.extend(GosnSerializedName(attribute_name).split('\n'));
        lines.extend(Field(attribute_name, typ).split('\n'))
        lines.append('')
        
    lines.extend(Constructor(type_name).split('\n'))
    lines.append('')
    
    # getters and setters
    for attribute_name in sorted(attributes):
        attribute_type, children = attributes[attribute_name]
        if attribute_type == LIST or attribute_type == OBJCET:
            attribute_type = children[0]
            
        lines.extend(Accessors(attribute_name, attribute_type).split('\n'))  
    
    lines.insert(0, Header(type_name, isGson));
    
    # print Header(type_name)
    # print '    ' + '\n    '.join(lines)
    # for line in lines:
        # if not line:
        #     print line
        # else:
        #     print '    ' + line
    # print Footer()
    content = "\n    ".join(lines)
    return content + "\n" + Footer();
    

def Header(type_name, isGson=False):
    interfaces = INTERFACES.get(type_name, DEFAULT_INTERFACES)
    import_names = CLASS_IMPORTS.get(type_name, DEFAULT_CLASS_IMPORTS)
    if import_names:
        imports = ';\n'.join(import_names) + ';'
        pass
    else:
        imports = ''
    if isGson :
        interfaces = ''
    else:
        interfaces = ' implements ' + ', '.join(interfaces)
    
    return HEADER % {'type_name': type_name,
                   'interfaces': interfaces ,
                   'imports': imports,
                   'timestamp': datetime.datetime.now(),
                   'package':PACKAGE}

# 构造函数
def Constructor(type_name):
    return 'public %s() {\n}' % type_name

def Field(attribute_name, attribute_type):
    """Print the field declarations."""
    replacements = AccessorReplacements(attribute_name, attribute_type)
    return '%(annotate)sprivate %(attribute_type)s %(field_name)s;' % replacements


def GosnSerializedName(attribute_name):
    return '@SerializedName("%s")' % attribute_name

def Accessors(name, attribute_type):
    """Print the getter and setter definitions."""
    replacements = AccessorReplacements(name, attribute_type)
    if attribute_type == BOOLEAN:
        return '%s\n%s' % (BOOLEAN_GETTER % replacements, SETTER % replacements)
    else:
        return '%s\n%s' % (GETTER % replacements, SETTER % replacements)

def Footer():
    return '}'

def AccessorReplacements(attribute_name, attribute_type):
    # 驼峰命名
    camel_name = ''.join([word.capitalize() for word in attribute_name.split('_')])
    # 驼峰命名首字母小写
    attribute_name = (camel_name[0].lower() + camel_name[1:])
    # 字段名称
    field_attribute_name = 'm' + camel_name
    
    annotat = ''
    if attribute_type == TODO:
        annotat = '//'
    return {
            'attribute_name': attribute_name,
            'camel_name': camel_name,
            'field_name': field_attribute_name,
            'attribute_type': attribute_type,
            'annotate': annotat,
    }
    
##############################################################################################
PARSER = """\
/**
 * Copyright 2014 Galen Wu
 */
package %(package)s.parsers;

import org.json.JSONException;
import org.json.JSONObject;

import com.androidex.appformwork.parsers.AbstractParser;
import com.androidex.appformwork.parsers.GroupParser;
/**
 * Auto-generated: %(timestamp)s
 *
 * @author Galen Wu (wuzhenlin135@126.com)
 * @param <T>
 */
public class %(type_name)sParser extends AbstractParser<%(type_name)s> {

    @Override
    public %(type_name)s parse(JSONObject json) throws JSONException {
        %(type_name)s obj = new %(type_name)s();
        
        %(stanzas)s
        
        return obj;
    }
}"""

BOOLEAN_STANZA = """\
        if (json.has("%(attr_name)s")) {
            obj.set%(attr_camel_name)s(json.getBoolean("%(attr_name)s")));
        }
"""

LIST_STANZA = """\
        if (json.has("%(attr_name)s")) {
            obj.set%(attr_camel_name)s(new GroupParser(new %(attr_camel_name)sParser()).parse(json.getJSONArray("%(attr_name)s")));
        }
"""

OBJ_STANZA = """\
        if (json.has("%(attr_name)s")) {
            obj.set%(attr_camel_name)s(new %(attr_camel_name)sParser().parse(json.getJSONObject("%(attr_name)s")));
        }
"""

STREING_STANZA = """\
        if (json.has("%(attr_name)s")) {
            obj.set%(attr_camel_name)s(json.getString("%(attr_name)s"));
        }
"""

INT_STANZA = """\
        if (json.has("%(attr_name)s")) {
            obj.set%(attr_camel_name)s(json.getInt("%(attr_name)s"));
        }
"""

DOUBLE_STANZA = """\
        if (json.has("%(attr_name)s")) {
            obj.set%(attr_camel_name)s(json.getDouble("%(attr_name)s"));
        }
"""

TODO_STANZA = """\
        if (json.has("%(attr_name)s")) {
            //TODO unknown type
        }
"""


def GenerateClass_parser(type_name, attributes):
    stanzas = []
    # sorted(attributes):
    for name in sorted(attributes):
        typ, children = attributes[name]
        replacements = Replacements(type_name, name)
        if typ == BOOLEAN:
            stanzas.append(BOOLEAN_STANZA % replacements)
        elif typ == INT:
            stanzas.append(INT_STANZA % replacements)
        elif typ == DOUBLE:
            stanzas.append(DOUBLE_STANZA % replacements)
        elif typ == STRING:
            stanzas.append(STREING_STANZA % replacements)
        elif typ == OBJCET:
            stanzas.append(OBJ_STANZA % replacements)
        elif typ == LIST:
            stanzas.append(LIST_STANZA % replacements)
        elif typ == TODO:
            stanzas.append(TODO_STANZA % replacements)
        else:
            stanzas.append(TODO_STANZA % replacements)

    replacements = Replacements(type_name, name)

    replacements['stanzas'] = '\n'.join(stanzas).strip()
    # print PARSER % replacements
    return PARSER % replacements

def Replacements(type_name, name):
    camel_name = ''.join([word.capitalize() for word in name.split('_')])
    return {
        'type_name': type_name,
        'timestamp': datetime.datetime.now(),
        'attr_name': name,
        'attr_camel_name': camel_name,
        'package':PACKAGE,
    }

if __name__ == '__main__' :
    main()
