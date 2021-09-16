import { HTTP_INTERCEPTORS, HttpClient, HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateLoader, TranslateModule, TranslateService } from '@ngx-translate/core';
import { ToastrModule } from 'ngx-toastr';

import { AppComponent } from '~/app/app.component';
import { AppRoutingModule } from '~/app/app-routing.module';
import { CoreModule } from '~/app/core/core.module';
import { getCurrentLanguage, setTranslationService, TranslateHttpLoader } from '~/app/i18n.helper';
import { PagesModule } from '~/app/pages/pages.module';
import { HttpErrorInterceptorService } from '~/app/shared/services/http-error-interceptor.service';

@NgModule({
  declarations: [AppComponent],
  imports: [
    HttpClientModule,
    BrowserModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    CoreModule,
    PagesModule,
    ToastrModule.forRoot({
      positionClass: 'toast-bottom-center',
      preventDuplicates: true
    }),
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
  constructor(translateService: TranslateService) {
    const language = getCurrentLanguage();
    translateService.setDefaultLang(language);
    setTranslationService(translateService);
  }
}
