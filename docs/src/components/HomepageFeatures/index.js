import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Behavioral Simulation',
    img: require('@site/static/img/behavioral_simulation.jpg').default,
    description: (
      <>
        Observe how different AI societies with distinct ethical and behavioral traits (like Altruism, Aggression, and Efficiency) interact and evolve.
      </>
    ),
  },
  {
    title: 'Dynamic Environments',
    img: require('@site/static/img/dynamic_environments.jpg').default,
    description: (
      <>
        Simulations run across varied scenarios such as Equilibrium, Abundance, and Famine, forcing the AI agents to constantly adapt to survive.
      </>
    ),
  },
  {
    title: 'Extensible ECS Engine',
    img: require('@site/static/img/ecs_engine.jpg').default,
    description: (
      <>
        Built on a highly optimized Entity-Component-System (ECS) architecture, allowing rapid iteration, scalability, and complex interactions.
      </>
    ),
  },
];

function Feature({img, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <img src={img} className={styles.featureSvg} alt={title} style={{borderRadius: '12px', boxShadow: '0 4px 15px rgba(0,0,0,0.2)', marginBottom: '1rem', objectFit: 'cover'}} />
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
