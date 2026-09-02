import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Behavioral Simulation',
    Svg: require('@site/static/img/undraw_docusaurus_mountain.svg').default,
    description: (
      <>
        Observe how different AI societies with distinct ethical and behavioral traits (like Altruism, Aggression, and Efficiency) interact and evolve.
      </>
    ),
  },
  {
    title: 'Dynamic Environments',
    Svg: require('@site/static/img/undraw_docusaurus_tree.svg').default,
    description: (
      <>
        Simulations run across varied scenarios such as Equilibrium, Abundance, and Famine, forcing the AI agents to constantly adapt to survive.
      </>
    ),
  },
  {
    title: 'Extensible ECS Engine',
    Svg: require('@site/static/img/undraw_docusaurus_react.svg').default,
    description: (
      <>
        Built on a highly optimized Entity-Component-System (ECS) architecture, allowing rapid iteration, scalability, and complex interactions.
      </>
    ),
  },
];

function Feature({Svg, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
