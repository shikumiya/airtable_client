# Python Airtable Client Library

## About - このライブラリについて

### [English]

This is an Airtable client library for python. This library has wrapped what is provided functions by Airtable API. When you use this library, you are able to easy implements Airtable's operations. Thereby, you are able to down a lot of costs what are implementing and maintenancing.

Make factory instance per a BASE. And make client instance per a table.

### [日本語]

Airtable用のPythonクライアントライブラリです。このライブラリはAirtable APIが提供している機能をラッピングしたものです。このライブラリを使えば容易にAirtableの操作を実装できます。それによって、実装コストやメンテナンスコストが大幅に低減できるでしょう。

ベース毎のファクトリインスタンスを生成し、テーブル毎にクライアントインスタンスを生成してください。

## Usage - 使用方法

### Install - インストール

```bash
pip install 'git+https://github.com/shikumiya/airtable_client.git'
```

### Preparation - 準備

You have to get a base key and an api key of Airtable. You are able to get them from Airtable API documents page write.

AirtableのベースIDとAPIキーを取得しておく必要があります。Airtableの各ベース毎のAPIドキュメントに記載されています。

```py
from airtable import AirtableClientFactory, AirtableSorter, SortDirection

AIRTABLE_BASE_KEY = 'YOUR BASE KEY'
AIRTABLE_API_KEY = 'YOUR API KEY'
```

### Create a client instance - Clientの作成

```py
# Make factory instance.
# ベース毎にファクトリクラスのインスタンスを生成します。
atf = AirtableClientFactory(base_id=AIRTABLE_BASE_KEY, api_key=AIRTABLE_API_KEY)

# Make client instance.
# テーブル毎にクライアントクラスのインスタンスを生成します。
at = atf.create('TABLE NAME')
```

### Note #1 - ノート1

```py
# All interfaces return Airtabler class.
# When you would like to get all records contents, to use the 'get' method after call interfaces.
# 操作系の処理は全てAirtablerクラス型を返します。
# recordsの中身をdict型で取得したい場合はgetメソッドを使用してください。
# [Sample]
# - INPUT(JSON from HTTP r)
# {
#   'records': [
#      {
#        'id': 'xxxxxxxxx',
#        'fields': {
#          'Name': 'foo',
#          'Age': 16
#        }
#     }
#   ]
# }
#
# - OUTPUT(dictionary)
# {
#   'Name': 'foo',
#   'Age': 16
# }
output = at.get_all().get()
```

### Search - 検索

```py
# Searching by no conditions.
# 条件指定なしで検索しています。
r = at.get(view='Grid view')
# The 'records' property returns records contents with converted dictionary type are got from HTTP r json.
# recordsプロパティでレスポンスJSON内のrecordsをdictにしたものを取得します。
# [Sample]
# - INPUT(JSON from HTTP r)
# {
#   'records': [
#     {
#       'id': 'xxxxxxxxx',
#       'fields': {
#         'Name': 'aaa',
#         'Age': 16
#       },
#     {
#       'id': 'xxxxxxxxx',
#       'fields': {
#         'Name': 'bbb',
#         'Age': 18
#       }
#     }
#   ]
# }
#
# - OUTPUT(array)
# [
#   {
#     'id': 'xxxxxxxxx',
#     'fields': {
#       'Name': 'aaa',
#       'Age': 16
#      }
#   },
#   {
#     'id': 'xxxxxxxxx',
#     'fields': {
#       'Name': 'bbb',
#       'Age': 18
#     }
#   }
# ]
print(r.records)
# The 'offset' property returns page offset value for getting next page contents.
# offsetプロパティでページングのoffsetを取得します。
print(r.offset)
# The 'get' method returns records contents by dictionary type.
# getメソッドでrecordsの中身をdict型で取得します。
print(r.get())
# The 'get_ids' method returns record ids what are filtered from records contents.
# get_idsメソッドで取得されたレコードのidの配列を返します。
print(r.get_ids())
```

```py
# Search for matching records by specifying a value in one field.
# ひとつのフィールドに値を指定して、一致するレコードを検索しています。1ページ目のみ取得します。
r = at.get_by('Name', 'test', view='Grid view')
print(r.records)
print(r.offset)
```

```py
# Searching for matching records by specifying a conditional expression. Gets only the first page.
# 条件式を指定して、一致するレコードを検索しています。1ページ目のみ取得します。
r = at.get_by_formula('{Name}="test"', view='Grid view')
print(r.records)
print(r.offset)
```

```py
# Searching for records for all pages.
# 全ページ分のレコードを検索しています。
records = at.get_all(view='Grid view').get()
print(records)
```

```py
# Searching for records on all matching pages by specifying a value in one field.
# ひとつのフィールドに値を指定して、一致する全ページ分のレコードを検索しています。
records = at.get_all_by('Name', 'test', view='Grid view').get()
print(records)
```

```py
# Search a record is first of result list with sort and specify a view. Sorting is specified by a one-dimensional array of field names.
# 検索し、得られたリスト内の最初の1件を取得しています。ソートとビューを指定しています。ソートはフィールド名の一次元配列で指定しています。
record = at.first().get()
print(record)
```

#### Sort - ソート

```py
# Search a record is first of result list with sort and specify a view. Sorting is specified by a one-dimensional array of field names.
# 検索し、得られたリスト内の最初の1件を取得しています。ソートとビューを指定しています。ソートはフィールド名の一次元配列で指定しています。
record = at.first(sort=['Name'], view='Grid view').get()
print(record)

# The sort argument is a dictionary value that specifies the field name and sort order (ascending / descending).
# ソートはdictionary値でフィールド名とソート順(昇順/降順)を指定しています。
record = at.first(sort={'field': 'Name', 'direction': 'asc'}).get()
print(record)

# The sort argument is specified by an array in the dictionary.
# ソートはdictionaryの配列で指定しています。
print('first: sort is list.dict')
record = at.first(sort=[{'field': 'Name', 'direction': 'asc'}]).get()
print(record)

# To make it easier to create a sort, specify the fields to sort in the AirtableSorter class.
# ソートを便利に構築するためのAirtableSorterクラスでソートするフィールドを指定しています。
print('first: sort is AirtableSorter')
record = at.first(sort=AirtableSorter().append('Name')).get()
print(record)

# The AirtableSorter class makes it easy to create a sort by specifying the fields to sort and the sort order.
# ソートを便利に構築するためのAirtableSorterクラスでソートするフィールドとソート順を指定しています。
print('first: sort is AirtableSorter with direction')
record = at.first(sort=AirtableSorter().append('Name', SortDirection.ASC)).get()
print(record)
```

```py
# Searching by specifying a unique ID that is internally assigned to each record in Airtable. Get only the first one.
# Airtableの各レコードに内部的に振られているユニークなIDを指定して検索しています。先頭の1件のみ取得します。
record = at.find(record['id'], view='Grid view').get()
print(record)
```

```py
# Searching for matching records by specifying a value in one field. Get only the first one.
# ひとつのフィールドに値を指定して、一致するレコードを検索しています。先頭の1件のみ取得します。
record = at.find_by('Name', 'test', view='Grid view').get()
print(record)
```

```py
# Searching for matching records by specifying conditional expression. Get only the first one.
# 条件式を指定して、一致するレコードを検索しています。先頭の1件のみ取得します。
record = at.find_by_formula('{Name}="test"', view='Grid view').get()
print(record)
```

### Register - 登録

```py
# One record is newly registered. Pass a fields what is dict type.
# fields（dict型）を作成し、1件のレコードを新規登録しています。
# [Sample]
# - fields(dict)
# {
#   'Name': 'foo',
#   'Age': 16
# }
record = at.insert(fields=fields).get()
print(record)

# Register multiple records at once. Create an array of fields and pass it.
# 複数のレコードを一括で新規登録しています。fieldsの配列を作成して渡します。
# [Sample]
# - fields_list(list)
# [
#   {'Name': 'aaa', 'Age': 16},
#   {'Name': 'bbb', 'Age': 18}
# ]
records = at.bulk_insert(fields_list=[fields, fields]).get()
print(records)
```

### Update - 更新

```py
# The target record is updated by specifying the record ID. Create and pass a fields for the item you would like to overwrite.
# レコードIDを指定して、対象のレコードを更新しています。上書きする項目のfieldsを作成して渡します。
record = at.update(id, fields).get()
print(record)
```

### Delete - 削除

```py
# The target record is deleted by specifying the record ID.
# レコードIDを指定して、対象のレコードを削除しています。
record = at.delete(id).get()
print(record)

# All records that match the criteria are specified and the records are deleted at once.
# 条件に一致する全てのレコードIDを指定して、一括でレコードを削除しています。
# [Sample]
# - ids(list)
# ['ID001', 'ID002', 'ID003]
records = at.bulk_delete(ids=ids).get()
print(records)

# You are able to also specify records and delete the records at once. All records must contain a record ID.
# recordsを指定して、一括でレコードを削除することもできます。recordsはidを含んでいる必要があります。
# [Sample]
# - records(list)
# [
#   {
#     'id': 'xxxxxxxxx',
#     'fields': {...}
#   },
#   {
#     'id': 'xxxxxxxxx',
#     'fields': {...}
#   },
#   {
#     'id': 'xxxxxxxxx',
#     'fields': {...}
#   }
# ]
records = at.bulk_delete(records=records).get()
print(records)
```
