import { HTTP_INTERCEPTORS, HttpClient, HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateLoader, TranslateModule, TranslateService } from '@ngx-translate/core';

import { AppComponent } from '~/app/app.component';
import { AppRoutingModule } from '~/app/app-routing.module';
import { CoreModule } from '~/app/core/core.module';
import { setTranslationService, TranslateHttpLoader } from '~/app/i18n.helper';
import { MaterialModule } from '~/app/material.modules';
import { PagesModule } from '~/app/pages/pages.module';
import { HttpErrorInterceptorService } from '~/app/shared/services/http-error-interceptor.service';
import { LocalStorageService } from '~/app/shared/services/local-storage.service';

@NgModule({
  declarations: [AppComponent],
  imports: [
    HttpClientModule,
    BrowserModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    CoreModule,
    MaterialModule,
    PagesModule,
    TranslateModule.forRoot({
      loader: {
        provide: TranslateLoader,
        useFactory: (http: HttpClient) => new TranslateHttpLoader(http),
        deps: [HttpClient]
      }
    })
  ],
  providers: [
    {
      provide: HTTP_INTERCEPTORS,
      useClass: HttpErrorInterceptorService,
      multi: true
    }
  ],
  bootstrap: [AppComponent]
})
export class AppModule {
  constructor(localStorageService: LocalStorageService, translateService: TranslateService) {
    const language = localStorageService.get('language', 'en_GB') as string;
    translateService.setDefaultLang(language);
    setTranslationService(translateService);
  }
}
