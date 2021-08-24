import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { TranslateModule } from '@ngx-translate/core';

import { CoreModule } from '~/app/core/core.module';
import { InstallerLayoutComponent } from '~/app/core/layouts/installer-layout/installer-layout.component';

describe('InstallerLayoutComponent', () => {
  let component: InstallerLayoutComponent;
  let fixture: ComponentFixture<InstallerLayoutComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CoreModule, RouterTestingModule, TranslateModule.forRoot()]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(InstallerLayoutComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
