import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TranslateModule } from '@ngx-translate/core';

import { ComponentsModule } from '~/app/shared/components/components.module';
import { LanguageButtonComponent } from '~/app/shared/components/language-button/language-button.component';

describe('LanguageButtonComponent', () => {
  let component: LanguageButtonComponent;
  let fixture: ComponentFixture<LanguageButtonComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ComponentsModule, HttpClientTestingModule, TranslateModule.forRoot()]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(LanguageButtonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
