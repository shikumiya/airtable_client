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
  ASC = 'asc'
  DESC = 'desc'


class AirtableSorter:

  def __init__(self):
    self.sort = []
    pass
  
  def append(self, field, direction=SortDirection.ASC):

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

class AirtableEntity(object):

  def __init__(self, records=[], offset=None):
    self.records = records
    self.offset = offset
    pass
  
  def size(self):
    return len(self.records)

  def get(self, index=None):
    if self.size() == 1:
      return self.records[0]
    elif self.size() > 1:
      if index:
        return self.records[index]
      else:
        return self.records
    else:
      return []
  
  def get_ids(self):
    return [record['id'] for record in self.get()]

class AirtableAuth(AuthBase):
  
    def __init__(self, api_key):
        self.api_key = api_key

    def __call__(self, r):
        r.headers['Authorization'] = 'Bearer ' + self.api_key
        return r

class AirtableClient(object):

  VERSION = 'v0'
  API_BASE_URL = 'https://api.airtable.com'
  API_URL = posixpath.join(API_BASE_URL, VERSION)
  API_LIMIT = 1.0 / 5  # 5 per second
  MAX_RECORDS_PER_REQUEST = 10

  def __init__(self, base_id, table_name, api_key, debug=False):

    session = requests.Session()
    session.auth = AirtableAuth(api_key=api_key)
    self.session = session

    self.debug = debug

    self.BASE_URL = posixpath.join(self.API_URL, base_id, quote(table_name))
    pass
  
  def _make_single_condition(self, field, value):
    return '{' + str(field) + '}="' + str(value) + '"'

  def _make_params(self, formula=None, offset=None, sort=None, max_records=None, fields=None):
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

    return p
  
  def _process_response_error(self, response):
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
    result_dict = self._process_response_error(response)
    if self.debug:
      print(result_dict)
    
    if 'error' in result_dict:
      return {'records': []}
    else:
      return result_dict

  def _request(self, method, url, params=None, json_data=None):
    response = self.session.request(method, url, params=params, json=json_data)
    if self.debug:
      print(response.url)
    
    return self._process_response(response)

  def _get(self, formula=None, offset=None, sort=None, max_records=None, fields=None):
    url = self.BASE_URL
    p = self._make_params(formula, offset, sort, max_records, fields)
    return self._request('get', url, params=p)

  def _post(self, data):
    url = self.BASE_URL
    return self._request('post', url, json_data=data)

  def _patch(self, id, data):
    url = posixpath.join(self.BASE_URL, id)
    return self._request('patch', url, json_data=data)

  def _delete(self, id):
    url = posixpath.join(self.BASE_URL, id)
    return self._request('delete', url)

  def _chunk(self, iterable, length):
      for i in range(0, len(iterable), length):
          yield iterable[i : i + length]

  def _build_batch_record_objects(self, records):
    return [{"fields": record} for record in records]

  def find(self, id, fields=None):
    return self.find_by_formula('RECORD_ID()="' + str(id) + '"', fields=fields)
  
  def find_by(self, field, value, sort=None, fields=None):
    return self.find_by_formula(self._make_single_condition(field, value), sort=sort, fields=fields)

  def find_by_formula(self, formula, sort=None, fields=None):
    return self.get_by_formula(formula, sort=sort, max_records=1, fields=fields)
  
  def first(self, sort=None, fields=None):
    return self.get(sort=sort, max_records=1, fields=fields)
  
  def get(self, offset=None, sort=None, max_records=None, fields=None):
    r = self._get(offset=offset, sort=sort, max_records=max_records, fields=fields)
    return AirtableEntity(records=r.get('records', []), offset=r.get('offset', None))

  def get_by(self, field, value, offset=None, sort=None, max_records=None, fields=None):
    return self.get_by_formula(self._make_single_condition(field, value), offset=offset, sort=sort, max_records=max_records, fields=fields)

  def get_by_formula(self, formula, offset=None, sort=None, max_records=None, fields=None):
    r = self._get(formula=formula, offset=offset, sort=sort, max_records=max_records, fields=fields)
    return AirtableEntity(records=r.get('records', []), offset=r.get('offset', None))
  
  def get_all(self, formula=None, sort=None, fields=None):
    offset = None

    all_records = []

    while True:
      r = self._get(formula=formula, offset=offset, sort=sort, fields=fields)
      if len(r) == 0:
        break
      records = r.get('records')
      all_records.extend(records)
      offset = r.get('offset')
      if not offset:
        break
      time.sleep(self.API_LIMIT)
    
    return AirtableEntity(records=all_records)
  
  def get_all_by(self, field, value, sort=None, fields=None):
    return self.get_all(self._make_single_condition(field, value), sort=sort, fields=fields)

  def insert(self, fields):
    return AirtableEntity(records=self._post(data={'fields': fields}))

  def bulk_insert(self, records):
    inserted_records = []
    for chunk in self._chunk(records, self.MAX_RECORDS_PER_REQUEST):
        new_records = self._build_batch_record_objects(chunk)
        r = self._post(data={"records": new_records})
        inserted_records += r["records"]
        time.sleep(self.API_LIMIT)
    return AirtableEntity(records=inserted_records)

  def update(self, id, fields):
    return AirtableEntity(records=self._patch(id, data={'fields': fields}))

  def delete(self, id):
    return AirtableEntity(records=self._delete(id))

  def bulk_delete(self, ids=[], records=[]):
    deleted_records = []

    if ids:
      for id in ids:
        r = self._delete(id)
        deleted_records.append(r)
        time.sleep(self.API_LIMIT)
    
    if records:
      ids = [record['id'] for record in records]
      for id in ids:
        r = self._delete(id)
        deleted_records.append(r)
        time.sleep(self.API_LIMIT)

    return AirtableEntity(records=deleted_records)

class AirtableClientFactory:

  def __init__(self, base_id=None, api_key=None, debug=False):
    self.base_id = base_id
    self.api_key = api_key
    self.debug = debug
    pass

  def create(self, table_name, base_id=None, api_key=None):

    if base_id:
      self.base_id = base_id
    if api_key:
      self.api_key = api_key
    
    if not self.base_id or not self.api_key:
      raise ValueError("'base_id' and 'api_key' are required. Please through args to constructor or this method.")

    return AirtableClient(self.base_id, table_name, self.api_key, debug=self.debug)
