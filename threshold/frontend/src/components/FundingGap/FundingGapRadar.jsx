import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { api } from '../../utils/api';
import { useNavigate } from 'react-router-dom';

export default function FundingGapRadar() {
  const containerRef = useRef();
  const navigate = useNavigate();
  const [data, setData] = useState([]);
  
  useEffect(() => {
    api.getFundingGap().then(d => setData(d));
  }, []);

  useEffect(() => {
    if (!data.length || !containerRef.current) return;
    containerRef.current.innerHTML = '';
    
    const width = containerRef.current.clientWidth;
    const height = 600;
    
    const svg = d3.select(containerRef.current)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('background', '#0A1628');
      
    // Scales
    const xScale = d3.scaleLinear().domain([0, 10]).range([50, width - 50]);
    const yScale = d3.scaleLinear().domain([0, 20000000]).range([height - 50, 50]); // Y logic inverted visually
    const rScale = d3.scaleSqrt().domain([1000000, 400000000]).range([10, 40]);
    
    // Grid Lines
    svg.append('line').attr('x1', width/2).attr('y1', 0).attr('x2', width/2).attr('y2', height).attr('stroke', '#2C3E50').attr('stroke-dasharray', '4,4');
    svg.append('line').attr('x1', 0).attr('y1', height/2).attr('x2', width).attr('y2', height/2).attr('stroke', '#2C3E50').attr('stroke-dasharray', '4,4');

    // Quadrant Labels
    svg.append('text').attr('x', 60).attr('y', 40).attr('fill', '#BDC3C7').text('OVERFUNDED');
    svg.append('text').attr('x', width-160).attr('y', 40).attr('fill', '#14BDAC').text('WELL-SERVED');
    svg.append('text').attr('x', 60).attr('y', height-30).attr('fill', '#0D7377').text('STABLE/MONITOR');
    svg.append('text').attr('x', width-160).attr('y', height-30).attr('fill', '#C0392B').text('DANGER ZONE').attr('font-weight', 'bold');

    // Color logic
    const getColor = (score) => {
        if (score >= 8) return '#C0392B';
        if (score >= 6) return '#E67E22';
        if (score >= 4) return '#F1C40F';
        return '#0D7377';
    };

    // Draw Bubbles
    const node = svg.append('g')
      .selectAll('circle')
      .data(data)
      .enter()
      .append('circle')
      .attr('r', d => rScale(d.population_affected || 5000000))
      .attr('cx', d => xScale(d.threshold_score))
      .attr('cy', d => yScale(d.funding_gap))
      .style('fill', d => getColor(d.threshold_score))
      .style('fill-opacity', 0.7)
      .style('stroke', d => getColor(d.threshold_score))
      .style('stroke-width', 2)
      .on('mouseover', function() { d3.select(this).style('fill-opacity', 1); })
      .on('mouseout', function() { d3.select(this).style('fill-opacity', 0.7); })
      .on('click', (e, d) => navigate(`/region/${d.region_id}`));

    // Labels
    svg.append('g')
      .selectAll('text')
      .data(data)
      .enter()
      .append('text')
      .attr('x', d => xScale(d.threshold_score))
      .attr('y', d => yScale(d.funding_gap))
      .attr('dy', d => -rScale(d.population_affected || 5000000) - 5)
      .attr('text-anchor', 'middle')
      .style('fill', '#fff')
      .style('font-size', '10px')
      .style('pointer-events', 'none')
      .text(d => d.name);
      
  }, [data, navigate]);

  return <div ref={containerRef} className="w-full border border-grey-dark rounded-xl overflow-hidden shadow-2xl" />;
}
