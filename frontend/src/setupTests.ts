// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

jest.mock('react-leaflet', () => {
	const mockReact = require('react');
	return {
	MapContainer: ({ children }: { children: unknown }) => mockReact.createElement('div', { 'data-testid': 'map-container' }, children),
	TileLayer: () => null,
	Marker: ({ children }: { children: unknown }) => mockReact.createElement('div', null, children),
	Popup: ({ children }: { children: unknown }) => mockReact.createElement('div', null, children),
	Polyline: () => null,
	};
});
