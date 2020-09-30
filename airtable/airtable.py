# -*- coding: utf-8 -*-
"""Python Airtable Client Library

This is an Airtable client library for python.
This library has wrapped what is provided functions by Airtable API.
When you use this library, you are able to easy implements Airtable's operations.
Thereby, you are able to down a lot of costs what are implementing and maintenancing.

Make factory instance per a BASE. And make client instance per a table.

Airtable用のPythonクライアントライブラリです。
このライブラリはAirtable APIが提供している機能をラッピングしたものです。
このライブラリを使えば容易にAirtableの操作を実装できます。
それによって、実装コストやメンテナンスコストが大幅に低減できるでしょう。

ベース毎のファクトリインスタンスを生成し、テーブル毎にクライアントインスタンスを生成してください。

Insipred by gtalarico/airtable-python-wrapper. It is also great library, thanks.
(https://github.com/gtalarico/airtable-python-wrapper)
"""
import requests
import json
import posixpath
import time
from urllib.parse import quote
from urllib.parse import urlencode
import enum
import sys
from requests.auth import AuthBase


class SortDirection(enum.Enum):
  """ソート順の列挙型

  sortオプションに渡す値です。

  :param ASC: 昇順
  :type ASC: string
  :param DESC: 降順
  :type DESC: string
  """
  ASC = 'asc'
  DESC = 'desc'


class AirtableSorter:
  """ソートの設定を構築するクラス
  """
  def __init__(self):
    """コンストラクタ
    """
    self.sort = []
    pass
  
  def append(self, field, direction=SortDirection.ASC):
    """ソートの設定を追加

    チェーンメソッド方式で追加できます。

    >>> sorter = AirtableSorter()
    >>> sorter.append('FieldA').append('FieldB', SortDirection.DESC)

    :param field: ソート対象のフィールド名
    :type field: string
    :param direction: ソート順, defaults to SortDirection.ASC
    :type direction: SortDirection, optional
    :return: self
    :rtype: AirtableSorter
    """
    if type(direction) is SortDirection:
      direction_value = direction.value
    else:
      direction_value = direction

    self.sort.append({
        'field': field,
        'direction': direction_value
    })
    #print(self.sort)
    return self
  
  def build(self):
    """sortのクエリパラメータを構築

    appendで追加されたソート順にパラメータを構築します。

    >>> query = sorter.build()

    :return: クエリパラメータのオブジェクト
    :rtype: dict
    """
    query = {}
    idx = 0
    for item in self.sort:
      #print(item)
      field = item['field']
      direction = item['direction']

      query['sort[' + str(idx) + '][field]'] = field
      query['sort[' + str(idx) + '][direction]'] = direction

      idx += 1
    
    return query

  @classmethod
  def make_params(self, params, sort):
    """クエリパラメータオブジェクトにsortを追加

    リクエスト用のクエリパラメータを構築します。
    クエリパラメータ用のオブジェクトは以下のクエリパラメータを設定します。
      sort[0][field]={field}&sort[0][direction]={direction}&sort[1][field]={field}&sort[1][direction]={direction}...&sort[n][field]={field}&sort[n][direction]={direction}
    sortパラメータは3種類の形式で指定可能です。

    - AirtableSorter
      appendを用いた設定済みのAirtableSorterオブジェクト
    
    - dict型の単一フィールド指定
    >>>
      {
        'field': 'field0',
        'direction': 'asc'
      }
    
    - list型の複数フィールド指定
    >>>
      [
        {'field': 'field0', 'direction': 'asc'},
        {'field': 'field1', 'direction': 'asc'},
        {'field': 'field2', 'direction': 'asc'}
      ]

    :param params: クエリパラメータ構築用のオブジェクト
    :type params: dict
    :param sort: ソート順
    :type sort: AirtableSorter|dict|list
    :return: クエリパラメータオブジェクト
    :rtype: dict
    """
    p = params

    if type(sort) is AirtableSorter:
      p.update(sort.build())
    elif isinstance(sort, dict):
      p['sort[0][field]'] = sort['field']
      if 'direction' in sort:
        p['sort[0][direction]'] = sort['direction']
      else:
        p['sort[0][direction]'] = SortDirection.ASC.value
    elif isinstance(sort, list):
      cnt = 0
      for sort_item in sort:
        if isinstance(sort_item, dict):
          p['sort[' + str(cnt) + '][field]'] = sort_item['field']
          if 'direction' in sort_item:
            p['sort[' + str(cnt) + '][direction]'] = sort_item['direction']
          else:
            p['sort[' + str(cnt) + '][direction]'] = SortDirection.ASC.value
        else:
          p['sort[' + str(cnt) + '][field]'] = sort_item
          p['sort[' + str(cnt) + '][direction]'] = SortDirection.ASC.value
        cnt += 1
    else:
      pass
    return p

class AirtableResponse(object):
  """レスポンスクラス

  :param object: objectを継承
  :type object: object
  """
  def __init__(self, records=[], offset=None, errors=[]):
    """コンストラクタ

    :param records: HTTPレスポンスのrecords, defaults to []
    :type records: list, optional
    :param offset: HTTPレスポンスから返却されるページオフセット値, defaults to None
    :type offset: string, optional
    :param error: HTTPレスポンスから返却されるエラー文言, defaults to None
    :type error: list, optional
    """
    self._records = records
    self._offset = offset
    self._errors = errors
    pass

  @property
  def records(self):
    """recordsのgetter

    >>> print(r.records)
    [
      {'id': 'XXX', 'fields': {...}},
      {'id': 'XXX', 'fields': {...}},
      {'id': 'XXX', 'fields': {...}}
    ]

    :return: コンストラクタにセットしたrecords
    :rtype: list
    """
    return self._records
  
  @property
  def offset(self):
    """offsetのgetter

    :return: コンストラクタにセットしたoffset
    :rtype: string
    """
    return self._offset

  @property
  def errors(self):
    """errorsのgetter

    :return: コンストラクタにセットしたerrors
    :rtype: list
    """
    return self._errors
  
  def size(self):
    """recordsの要素数を取得

    :return: recordsの要素数(=レコード数)
    :rtype: int
    """
    return len(self.records)

  def get(self, index=None):
    """recordsを取得

    0〜n件のレコードを返却。要素番号を指定した場合は、その要素のレコードを返却。

    >>> print(r.get())
    [
      {'id': 'XXX', 'fields': {...}},
      {'id': 'XXX', 'fields': {...}},
      {'id': 'XXX', 'fields': {...}}
    ]

    :param index: recordsの要素番号, defaults to None
    :type index: int, optional
    :return: 0〜n件のレコード
    :rtype: list
    """
    if self.size() == 1:
      return self._records[0]
    elif self.size() > 1:
      if index:
        return self._records[index]
      else:
        return self._records
    else:
      return []
  
  def get_ids(self):
    """レコードIDのリストを取得

    >>> print(r.get_ids())
    ['XXX', 'XXX', 'XXX']

    :return: レコードIDの一次元配列
    :rtype: list
    """
    return [record['id'] for record in self.get()]

class AirtableAuth(AuthBase):
  """Airtableの認証クラス

  :param AuthBase: AuthBaseクラスを継承
  :type AuthBase: requests.auth.AuthBase
  """
  def __init__(self, api_key):
    """コンストラクタ

    :param api_key: AirtableのAPIキー
    :type api_key: string
    """
    self.api_key = api_key

  def __call__(self, r):
    """リクエスト送信時に呼び出され、認証ヘッダーを付与する
    """
    r.headers['Authorization'] = 'Bearer ' + self.api_key
    return r

class AirtableClient(object):
  """Airtableクライアントクラス

  :param object: objectクラスを継承
  :type object: object
  """
  _VERSION = 'v0'
  _API_BASE_URL = 'https://api.airtable.com'
  _API_URL = posixpath.join(_API_BASE_URL, _VERSION)
  _API_LIMIT = 1.0 / 5  # 5 per second
  _MAX_RECORDS_PER_REQUEST = 10

  def __init__(self, base_id, table_name, api_key, debug=False):
    """コンストラクタ

    :param base_id: AirtableのBASE ID
    :type base_id: string
    :param table_name: Airtableのテーブル名
    :type table_name: string
    :param api_key: AirtableのAPIキー
    :type api_key: string
    :param debug: デバッグモードのフラグ(True:ON/False:OFF), defaults to False
    :type debug: bool, optional
    """
    session = requests.Session()
    session.auth = AirtableAuth(api_key=api_key)
    self.session = session

    self.debug = debug

    self.BASE_URL = posixpath.join(self._API_URL, base_id, quote(table_name))
    pass
  
  def _make_single_condition(self, field, value):
    """filterByFormulaのfield=value条件式を1つ構築して返却

    :param field: フィールド名
    :type field: string
    :param value: 検索値
    :type value: string
    :return: {field}=valueの文字列
    :rtype: string
    """
    return '{' + str(field) + '}="' + str(value) + '"'

  def _make_params(self, formula=None, offset=None, sort=None, max_records=None, fields=None, view=None):
    """リクエストパラメータを構築

    :param formula: filterByFormula値, defaults to None
    :type formula: string, optional
    :param offset: offset値, defaults to None
    :type offset: string, optional
    :param sort: sort値, defaults to None
    :type sort: AirtableSorter|dict|list, optional
    :param max_records: maxRecords値, defaults to None ※未指定の場合はデフォルトで100件
    :type max_records: int, optional
    :param fields: fields値, defaults to None
    :type fields: list, optional
    :param view: view値, defaults to None
    :type view: string, optional
    :return: リクエストパラメータのオブジェクト
    :rtype: dict
    """
    p = {}
    if formula:
      p['filterByFormula'] = formula
    if offset:
      p['offset'] = offset
    if sort:
      p = AirtableSorter.make_params(p, sort)
    if max_records:
      p['maxRecords'] = max_records
    if fields:
      p['fields'] = []
      for field in fields:
        p['fields'].append(field)
    if view:
      p['view'] = view

    return p
  
  def _process_response_error(self, response):
    """HTTPレスポンスのエラー処理

    :param response: レスポンスオブジェクト
    :type response: requests.Response
    :raises exc: HTTPErrorをキャッチした場合は送出
    :return: HTTPレスポンスボディのJSONオブジェクト
    :rtype: dict
    """
    try:
      response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
      err_msg = str(exc)

      try:
        error_dict = response.json()
      except ValueError:
        pass
      else:
        if "error" in error_dict:
          err_msg += " [Error: {}]".format(error_dict["error"])
      exc.args = (*exc.args, err_msg)
      raise exc
    else:
      return response.json()

  def _process_response(self, response):
    """HTTPレスポンスの事後処理

    :param response: レスポンスオブジェクト
    :type response: requests.Response
    :return: HTTPレスポンスボディのJSONオブジェクト
    :rtype: dict
    """
    result_dict = self._process_response_error(response)
    if self.debug:
      print(result_dict)
    
    if 'error' in result_dict:
      return {'records': [], 'error': result_dict['error']}
    else:
      return result_dict

  def _request(self, method, url, params=None, json_data=None):
    """HTTPリクエスト送信

    :param method: HTTPメソッド
    :type method: string
    :param url: リクエストURL
    :type url: string
    :param params: リクエストパラメータオブジェクト, defaults to None
    :type params: dict, optional
    :param json_data: リクエストJSONデータオブジェクト, defaults to None
    :type json_data: dict, optional
    :return: HTTPレスポンスボディのJSONオブジェクト
    :rtype: dict
    """
    response = self.session.request(method, url, params=params, json=json_data)
    if self.debug:
      print(response.url)
    
    return self._process_response(response)

  def _get(self, formula=None, offset=None, sort=None, max_records=None, fields=None, view=None):
    """GETリクエスト送信

    :param formula: filterByFormula値, defaults to None
    :type formula: string, optional
    :param offset: offset値, defaults to None
    :type offset: string, optional
    :param sort: sort値, defaults to None
    :type sort: AirtableSorter|dict|list, optional
    :param max_records: maxRecords値, defaults to None ※未指定の場合はデフォルトで100件
    :type max_records: int, optional
    :param fields: fields値, defaults to None
    :type fields: list, optional
    :param view: view値, defaults to None
    :type view: string, optional
    :return: HTTPレスポンスボディのJSONオブジェクト
    :rtype: dict
    """
    url = self.BASE_URL
    p = self._make_params(formula, offset, sort, max_records, fields, view)
    return self._request('get', url, params=p)

  def _post(self, data):
    """POSTリクエスト送信

    :param data: リクエストJSONデータオブジェクト
    :type data: dict
    :return: HTTPレスポンスボディのJSONオブジェクト
    :rtype: dict
    """
    url = self.BASE_URL
    return self._request('post', url, json_data=data)

  def _patch(self, id, data):
    """PATCHリクエスト送信

    :param data: リクエストJSONデータオブジェクト
    :type data: dict
    :return: HTTPレスポンスボディのJSONオブジェクト
    :rtype: dict
    """
    url = posixpath.join(self.BASE_URL, id)
    return self._request('patch', url, json_data=data)

  def _delete(self, id):
    """DELETEリクエスト送信

    :param data: リクエストJSONデータオブジェクト
    :type data: dict
    :return: HTTPレスポンスボディのJSONオブジェクト
    :rtype: dict
    """
    url = posixpath.join(self.BASE_URL, id)
    return self._request('delete', url)

  def _chunk(self, iterable, length):
    """チャンク処理(分割処理)

    :param iterable: 処理対象のイテラブルオブジェクト
    :type iterable: object
    :param length: チャンクサイズ
    :type length: int
    :yield: [description]
    :rtype: [type]
    """
    for i in range(0, len(iterable), length):
      yield iterable[i : i + length]

  def _build_batch_records(self, fields_list):
    """一括処理用のレコードリストを構築

    :param fields_list: fieldsのリスト
    :type fields_list: list
    :return: recordsにセットするリスト
    :rtype: list
    """
    return [{"fields": fields} for fields in fields_list]

  def find(self, id, fields=None, view=None):
    """レコードIDで検索（1件取得）

    >>> print(client.find('XXX').get())
    {
      'id': 'XXX',
      'fields': {
        'Name': 'aaa',
        'Age': 16
      }
    }

    :param id: 検索対象のレコードID
    :type id: string
    :param fields: レスポンスに含めるフィールド名のリスト, defaults to None
    :type fields: list, optional
    :param view: 検索対象のビュー名, defaults to None
    :type view: string, optional
    :return: 検索結果
    :rtype: AirtableResponse
    """
    return self.find_by_formula('RECORD_ID()="' + str(id) + '"', fields=fields, view=view)
  
  def find_by(self, field, value, sort=None, fields=None, view=None):
    """対象フィールドの値に一致するレコードを検索（先頭の1件取得）

    >>> print(client.find_by('Name', 'aaa').get())
    {
      'id': 'XXX',
      'fields': {
        'Name': 'aaa',
        'Age': 16
      }
    }

    :param field: 検索対象のフィールド名
    :type field: string
    :param value: 検索対象のフィールド値
    :type value: string
    :param sort: 検索結果のソート順, defaults to None
    :type sort: AirtableSorter|dict|list, optional
    :param fields: レスポンスに含めるフィールド名のリスト, defaults to None
    :type fields: list, optional
    :param view: 検索対象のビュー名, defaults to None
    :type view: string, optional
    :return: 検索結果
    :rtype: AirtableResponse
    """
    return self.find_by_formula(self._make_single_condition(field, value), sort=sort, fields=fields, view=view)

  def find_by_formula(self, formula, sort=None, fields=None, view=None):
    """条件式に一致するレコードを検索（先頭の1件取得）

    >>> print(client.find_by_formula('{Age}<20').get())
    {
      'id': 'XXX',
      'fields': {
        'Name': 'aaa',
        'Age': 16
      }
    }

    :param formula: 任意の条件式(Airtableのformulaを参照)
    :type formula: string
    :param sort: 検索結果のソート順, defaults to None
    :type sort: AirtableSorter|dict|list, optional
    :param fields: レスポンスに含めるフィールド名のリスト, defaults to None
    :type fields: list, optional
    :param view: 検索対象のビュー名, defaults to None
    :type view: string, optional
    :return: 検索結果
    :rtype: AirtableResponse
    """
    return self.get_by_formula(formula, sort=sort, max_records=1, fields=fields, view=view)
  
  def first(self, sort=None, fields=None, view=None):
    """条件指定なしで検索し、先頭の1件を取得

    >>> print(client.first().get())
    {
      'id': 'XXX',
      'fields': {
        'Name': 'aaa',
        'Age': 16
      }
    }

    :param sort: 検索結果のソート順, defaults to None
    :type sort: AirtableSorter|dict|list, optional
    :param fields: レスポンスに含めるフィールド名のリスト, defaults to None
    :type fields: list, optional
    :param view: 検索対象のビュー名, defaults to None
    :type view: string, optional
    :return: 検索結果
    :rtype: AirtableResponse
    """
    return self.get(sort=sort, max_records=1, fields=fields, view=view)
  
  def get(self, offset=None, sort=None, max_records=None, fields=None, view=None):
    """条件指定なしで検索し、1ページ分のレコードを取得

    >>> print(client.get().records) # recordsを抽出（Airtable APIのレスポンスそのまま）
    {
      'records': [
        {
          'id': 'XXX',
          'fields': {
            'Name': 'aaa',
            'Age': 16
          }
        },
        {
          'id': 'XXX',
          'fields': {
            'Name': 'bbb',
            'Age': 18
          }
        },
        {
          'id': 'XXX',
          'fields': {
            'Name': 'ccc',
            'Age': 16
          }
        }
      ]
    }

    >>> print(client.get().get()) # recordsの中身だけ抽出
    [
      {
        'id': 'XXX',
        'fields': {
          'Name': 'aaa',
          'Age': 16
        }
      },
      {
        'id': 'XXX',
        'fields': {
          'Name': 'bbb',
          'Age': 18
        }
      },
      {
        'id': 'XXX',
        'fields': {
          'Name': 'ccc',
          'Age': 16
        }
      }
    ]

    :param offset: ページングのオフセット値, defaults to None
    :type offset: string, optional
    :param sort: 検索結果のソート順, defaults to None
    :type sort: AirtableSorter|dict|list, optional
    :param max_records: 検索結果の上限レコード数, defaults to None
    :type max_records: int, optional
    :param fields: レスポンスに含めるフィールド名のリスト, defaults to None
    :type fields: list, optional
    :param view: 検索対象のビュー名, defaults to None
    :type view: string, optional
    :return: 検索結果
    :rtype: AirtableResponse
    """
    r = self._get(offset=offset, sort=sort, max_records=max_records, fields=fields, view=view)
    return AirtableResponse(records=r.get('records', []), offset=r.get('offset', None), errors=[r.get('error', None)])

  def get_by(self, field, value, offset=None, sort=None, max_records=None, fields=None, view=None):
    """対象フィールドの値に一致するレコードを検索（1ページ分のレコードを取得）

    >>> print(client.get_by('Age', '16').get())
    [
      {
        'id': 'XXX',
        'fields': {
          'Name': 'aaa',
          'Age': 16
        }
      },
      {
        'id': 'XXX',
        'fields': {
          'Name': 'ccc',
          'Age': 16
        }
      }
    ]

    :param field: 検索対象のフィールド名
    :type field: string
    :param value: 検索対象のフィールド値
    :type value: string
    :param offset: ページングのオフセット値, defaults to None
    :type offset: string, optional
    :param sort: 検索結果のソート順, defaults to None
    :type sort: AirtableSorter|dict|list, optional
    :param max_records: 検索結果の上限レコード数, defaults to None
    :type max_records: int, optional
    :param fields: レスポンスに含めるフィールド名のリスト, defaults to None
    :type fields: list, optional
    :param view: 検索対象のビュー名, defaults to None
    :type view: string, optional
    :return: 検索結果
    :rtype: AirtableResponse
    """
    return self.get_by_formula(self._make_single_condition(field, value), offset=offset, sort=sort, max_records=max_records, fields=fields, view=view)

  def get_by_formula(self, formula, offset=None, sort=None, max_records=None, fields=None, view=None):
    """条件式に一致するレコードを検索（1ページ分のレコードを取得）

    >>> print(client.get_by_formula('{Age}<20').get())
    [
      {
        'id': 'XXX',
        'fields': {
          'Name': 'aaa',
          'Age': 16
        }
      },
      {
        'id': 'XXX',
        'fields': {
          'Name': 'bbb',
          'Age': 18
        }
      },
      {
        'id': 'XXX',
        'fields': {
          'Name': 'ccc',
          'Age': 16
        }
      }
    ]

    :param formula: 任意の条件式(Airtableのformulaを参照)
    :type formula: string
    :param offset: ページングのオフセット値, defaults to None
    :type offset: string, optional
    :param sort: 検索結果のソート順, defaults to None
    :type sort: AirtableSorter|dict|list, optional
    :param max_records: 検索結果の上限レコード数, defaults to None
    :type max_records: int, optional
    :param fields: レスポンスに含めるフィールド名のリスト, defaults to None
    :type fields: list, optional
    :param view: 検索対象のビュー名, defaults to None
    :type view: string, optional
    :return: 検索結果
    :rtype: AirtableResponse
    """
    r = self._get(formula=formula, offset=offset, sort=sort, max_records=max_records, fields=fields, view=view)
    return AirtableResponse(records=r.get('records', []), offset=r.get('offset', None), errors=[r.get('error', None)])
  
  def get_all(self, formula=None, sort=None, fields=None, view=None):
    """全てのレコードを検索（全ページ）

    >>> print(client.get_all().get())
    [
      {
        'id': 'XXX',
        'fields': {
          'Name': 'aaa',
          'Age': 16
        }
      },
      {
        'id': 'XXX',
        'fields': {
          'Name': 'bbb',
          'Age': 18
        }
      },
      {
        'id': 'XXX',
        'fields': {
          'Name': 'ccc',
          'Age': 16
        }
      }
    ]

    :param formula: 任意の条件式(Airtableのformulaを参照)
    :type formula: string
    :param sort: 検索結果のソート順, defaults to None
    :type sort: AirtableSorter|dict|list, optional
    :param fields: レスポンスに含めるフィールド名のリスト, defaults to None
    :type fields: list, optional
    :param view: 検索対象のビュー名, defaults to None
    :type view: string, optional
    :return: 検索結果
    :rtype: AirtableResponse
    """
    offset = None

    all_records = []
    errors = []

    while True:
      r = self._get(formula=formula, offset=offset, sort=sort, fields=fields, view=view)
      if len(r) == 0:
        break
      records = r.get('records')
      error = r.get('error')
      if error:
        errors.append(error)
      all_records.extend(records)
      offset = r.get('offset')
      if not offset:
        break
      time.sleep(self._API_LIMIT)
    
    return AirtableResponse(records=all_records, errors=errors)
  
  def get_all_by(self, field, value, sort=None, fields=None, view=None):
    """対象フィールドの値に一致するレコードを検索（全ページ）

    >>> print(client.get_all_by('Age', '16').get())
    [
      {
        'id': 'XXX',
        'fields': {
          'Name': 'aaa',
          'Age': 16
        }
      },
      {
        'id': 'XXX',
        'fields': {
          'Name': 'ccc',
          'Age': 16
        }
      }
    ]

    :param field: 検索対象のフィールド名
    :type field: string
    :param value: 検索対象のフィールド値
    :type value: string
    :param sort: 検索結果のソート順, defaults to None
    :type sort: AirtableSorter|dict|list, optional
    :param fields: レスポンスに含めるフィールド名のリスト, defaults to None
    :type fields: list, optional
    :param view: 検索対象のビュー名, defaults to None
    :type view: string, optional
    :return: 検索結果
    :rtype: AirtableResponse
    """
    return self.get_all(self._make_single_condition(field, value), sort=sort, fields=fields, view=view)

  def insert(self, fields):
    """1件のレコードを新規登録

    >>> client.insert({'Name': 'ddd', 'Age': 25})

    :param fields: レコードのフィールド
    :type fields: dict
    :return: 登録結果
    :rtype: AirtableResponse
    """
    r = self._post(data={'fields': fields})
    return AirtableResponse(records=r)

  def bulk_insert(self, fields_list):
    """一括でレコードを新規登録

    >>> client.bulk_insert([{'Name': 'eee', 'Age': 23}, {'Name': 'fff', 'Age': 19})

    :param fields_list: レコードのフィールドリスト
    :type fields_list: list
    :return: 登録結果
    :rtype: AirtableResponse
    """
    inserted_records = []

    for chunk_records in self._chunk(fields_list, self._MAX_RECORDS_PER_REQUEST):
        new_records = self._build_batch_records(chunk_records)
        r = self._post(data={"records": new_records})
        inserted_records += r.get('records')
        time.sleep(self._API_LIMIT)
    return AirtableResponse(records=inserted_records)

  def update(self, id, fields):
    """対象のレコードを更新

    >>> client.update('XXX', {Age': 20})

    :param id: 更新対象のレコードID
    :type id: string
    :param fields: 更新対象のフィールド（指定されたフィールドのみ上書き）
    :type fields: dict
    :return: 更新結果
    :rtype: AirtableResponse
    """
    r = self._patch(id, data={'fields': fields})
    return AirtableResponse(records=r)

  def delete(self, id):
    """1件のレコードを削除

    >>> client.delete('XXX')

    :param id: 削除対象のレコードID
    :type id: string
    :return: 削除結果
    :rtype: AirtableResponse
    """
    r = self._delete(id)
    return AirtableResponse(records=r)

  def bulk_delete(self, ids=[], records=[]):
    """一括でレコードを削除

    >>> client.bulk_delete(ids=['XXX', 'XXX'])

    >>> client.bulk_delete(records=[{'id': 'XXX', 'fields': {...}}, {'id': 'XXX', 'fields': {...}}])

    :param ids: 削除対象のレコードIDリスト, defaults to []
    :type ids: list, optional
    :param records: 削除対象のレコードリスト(idを含めること), defaults to []
    :type records: list, optional
    :return: 削除結果
    :rtype: AirtableResponse
    """
    deleted_records = []

    # ids指定の場合
    if ids:
      for chunk_ids in self._chunk(ids, self._MAX_RECORDS_PER_REQUEST):
        for id in chunk_ids:
          r = self._delete(id)
          deleted_records.append(r)
        time.sleep(self._API_LIMIT)
    
    # records指定の場合
    if records:
      ids = [record['id'] for record in records]
      for chunk_ids in self._chunk(ids, self._MAX_RECORDS_PER_REQUEST):
        for id in chunk_ids:
          r = self._delete(id)
          deleted_records.append(r)
        time.sleep(self._API_LIMIT)

    return AirtableResponse(records=deleted_records)

class AirtableClientFactory:
  """AirtableClientのファクトリクラス

  ベース毎にインスタンスを生成してください。

  ベースIDとAPIキーは必須です。コンストラクタでベースIDとAPIキーを指定しない場合は、createメソッドをコールする際に指定してください。

  """
  def __init__(self, base_id=None, api_key=None, debug=False):
    """コンストラクタ

    :param base_id: AirtableのベースID, defaults to None
    :type base_id: string, optional
    :param api_key: AirtableのAPIキー, defaults to None
    :type api_key: string, optional
    :param debug: デバッグモードフラグ(True:ON/False:OFF), defaults to False
    :type debug: bool, optional
    """
    self.base_id = base_id
    self.api_key = api_key
    self.debug = debug
    pass

  def create(self, table_name, base_id=None, api_key=None):
    """Airtableクライアントのインスタンスを生成して返却

    1) ベース毎にインスタンスを生成する場合

    >>> factory = AirtableClientFactory(base_id='XXX', api_key='XXX')
    >>> client = factory.create(table_name='XXX')

    2) create時に毎回ベースを指定する場合

    >>> factory = AirtableClientFactory()
    >>> client = factory.create(table_name='XXX', base_id='XXX', api_key='XXX')

    :param table_name: Airtableのテーブル名
    :type table_name: string
    :param base_id: AirtableのベースID, defaults to None
    :type base_id: string, optional
    :param api_key: AirtableのAPIキー, defaults to None
    :type api_key: string, optional
    :raises ValueError: ベースIDとAPIキーを指定していない場合に送出される
    :return: Airtableクライアント
    :rtype: AirtableClient
    """
    if base_id:
      self.base_id = base_id
    if api_key:
      self.api_key = api_key
    
    if not self.base_id or not self.api_key:
      raise ValueError("'base_id' and 'api_key' are required. Please through args to constructor or this method.")

    return AirtableClient(self.base_id, table_name, self.api_key, debug=self.debug)
