import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DeploymentPageComponent } from './deployment-page.component';

describe('DeploymentPageComponent', () => {
  let component: DeploymentPageComponent;
  let fixture: ComponentFixture<DeploymentPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [DeploymentPageComponent]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DeploymentPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
