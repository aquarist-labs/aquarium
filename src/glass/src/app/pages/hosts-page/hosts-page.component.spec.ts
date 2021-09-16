import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TranslateModule } from '@ngx-translate/core';

import { HostsPageComponent } from '~/app/pages/hosts-page/hosts-page.component';
import { PagesModule } from '~/app/pages/pages.module';

describe('HostsPageComponent', () => {
  let component: HostsPageComponent;
  let fixture: ComponentFixture<HostsPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, PagesModule, TranslateModule.forRoot()]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(HostsPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
