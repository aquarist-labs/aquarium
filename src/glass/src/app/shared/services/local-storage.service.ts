import { Injectable } from '@angular/core';
import * as _ from 'lodash';

@Injectable({
  providedIn: 'root'
})
export class LocalStorageService {
  constructor() {}

  get(key: string, defaultValue?: any): string | null {
    const value = localStorage.getItem(key);
    return _.defaultTo(value, defaultValue);
  }

  set(key: string, value: string) {
    localStorage.setItem(key, value);
  }
}
