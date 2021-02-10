import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { InstallModePageComponent } from '~/app/pages/install-mode-page/install-mode-page.component';
import { PagesModule } from '~/app/pages/pages.module';

describe('InstallModePageComponent', () => {
  let component: InstallModePageComponent;
  let fixture: ComponentFixture<InstallModePageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PagesModule, HttpClientTestingModule, RouterTestingModule]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(InstallModePageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
