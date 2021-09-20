describe('Dive into Aquarium', () => {
  it('Visit the first tank', () => {
    cy.visit('/');
    cy.contains('Create new cluster');
    cy.clickButton('Create');
    cy.contains('Start');
    cy.contains('Networking');
    cy.contains('Time');
    cy.contains('Devices');
    cy.contains('Installation');
    cy.contains('Finish');
    cy.contains('Next');
    cy.clickButton('Next');
    cy.contains('Hostname');
    cy.contains('div', 'Hostname').find('input').type('foohost{enter}');
    cy.clickButton('Next');
    cy.contains('Use an NTP host on the Internet').click();
    cy.clickButton('Next');
    cy.clickButton('Next');
    cy.clickButton('Install');
  });
});
