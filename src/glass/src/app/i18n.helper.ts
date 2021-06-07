/*
 * Project Aquarium's frontend (glass)
 * Copyright (C) 2021 SUSE, LLC.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */
import { HttpClient } from '@angular/common/http';
import { TranslateService } from '@ngx-translate/core';
import { TranslateLoader } from '@ngx-translate/core';
import * as _ from 'lodash';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

let translateService: TranslateService;

export const setTranslationService = (service: TranslateService) => {
  translateService = service;
};

/**
 * Translate a string instantly.
 */
export const translate = (text: string): string =>
  _.isUndefined(translateService) ? text : translateService.instant(text);

/**
 * Load the specified translation file.
 */
export class TranslateHttpLoader implements TranslateLoader {
  constructor(private http: HttpClient) {}

  public getTranslation(lang: string): Observable<Record<string, string>> {
    return this.http.get<Record<string, string>>(`/assets/i18n/${lang}.json`).pipe(
      map((translations) =>
        // Remove empty translations.
        _.omitBy(translations, _.isEmpty)
      )
    );
  }
}

export const supportedLanguages: Record<string, string> = {
  /* eslint-disable @typescript-eslint/naming-convention */
  en_US: 'English',
  de_DE: 'Deutsch'
};

/**
 * Get the current configured language. If not set in local storage,
 * then try to get the default browser language. Finally fall back
 * to the specified default language. Defaults to 'en_US'.
 */
export const getCurrentLanguage = (defaultValue = 'en_US'): string => {
  // Get the stored language from local storage.
  let lang = localStorage.getItem('language');
  // If not set, try to detect the browser language.
  if (_.isNull(lang)) {
    if (_.isArray(navigator.languages)) {
      lang = _.chain<string>(navigator.languages)
        .filter((l: string) => l.includes('-'))
        .map((l: string) => l.replace('-', '_'))
        .filter((l: string) => _.has(supportedLanguages, l))
        .first()
        .value();
    }
  }
  return _.defaultTo(lang, defaultValue);
};

export const setCurrentLanguage = (lang: string): void => {
  localStorage.setItem('language', lang);
};
