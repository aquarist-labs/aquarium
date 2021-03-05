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
