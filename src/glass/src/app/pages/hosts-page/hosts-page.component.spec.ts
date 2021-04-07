import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';

import { HostsPageComponent } from '~/app/pages/hosts-page/hosts-page.component';
import { PagesModule } from '~/app/pages/pages.module';

describe('HostsPageComponent', () => {
  let component: HostsPageComponent;
  let fixture: ComponentFixture<HostsPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        NoopAnimationsModule,
        PagesModule,
        TranslateModule.forRoot()
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(HostsPageComponent);
    component = fixture.componentInstance;
    component.autoReload = 0;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
